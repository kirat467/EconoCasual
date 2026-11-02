"""Double Machine Learning for EconoCausal (Week 2, Member 2).

Estimates the Individual Treatment Effect (ITE) of a discount, i.e. how much each
customer's purchase probability changes if they are shown a discount.

Method (partially linear model, Chernozhukov et al. 2018):
    Y = theta(X) * T + g(X) + e        Y = purchase, T = discount dollars
    T = m(X) + v                       m(X) = how discounts were assigned

  1. CROSS-FIT two "nuisance" models with K folds, so every customer's prediction
     comes from a model that never saw that customer:
         Y_hat = E[Y | X]      T_hat = E[T | X]
  2. RESIDUALIZE:  Y_res = Y - Y_hat,  T_res = T - T_hat
     T_res is the part of the discount NOT explained by the confounders, which is
     "as good as random". Y_res is the part of purchasing not explained by them.
  3. FINAL STAGE: learn theta(X) from  Y_res = theta(X) * T_res + noise.
        'linear' -> OLS on T_res * polynomial(X)
        'gbm'    -> R-learner: regress Y_res / T_res on X with weights T_res^2

Run from the repo root:  python backend/casual_model.py
"""
from pathlib import Path

import numpy as np
import pandas as pd
from lightgbm import LGBMClassifier, LGBMRegressor
from sklearn.linear_model import Ridge
from sklearn.model_selection import KFold, train_test_split
from sklearn.preprocessing import PolynomialFeatures, StandardScaler

ROOT = Path(__file__).resolve().parent.parent
FEATURES = ["previous_purchases", "engagement", "price_sensitivity", "age"]


def _nuisance_model(seed):
    # Small, regularised trees: nuisance models should not overfit.
    return LGBMRegressor(n_estimators=200, learning_rate=0.05, num_leaves=8,
                         min_child_samples=30, subsample=0.8, subsample_freq=1,
                         colsample_bytree=0.8, random_state=seed, verbose=-1)


class DoubleML:
    def __init__(self, final="linear", n_splits=5, seed=0):
        assert final in ("linear", "gbm")
        self.final, self.n_splits, self.seed = final, n_splits, seed

    def fit(self, X, T, Y):
        X, T, Y = np.asarray(X, float), np.asarray(T, float), np.asarray(Y, float)
        y_hat, t_hat = np.zeros(len(Y)), np.zeros(len(T))

        # Step 1: cross-fitting
        for tr, te in KFold(self.n_splits, shuffle=True, random_state=self.seed).split(X):
            y_hat[te] = _nuisance_model(self.seed).fit(X[tr], Y[tr]).predict(X[te])
            t_hat[te] = _nuisance_model(self.seed).fit(X[tr], T[tr]).predict(X[te])

        # Step 2: residualise
        self.y_res_, self.t_res_ = Y - y_hat, T - t_hat

        # Step 3: final stage
        if self.final == "linear":
            self.scaler_ = StandardScaler().fit(X)
            self.poly_ = PolynomialFeatures(2, include_bias=True)
            phi = self.poly_.fit_transform(self.scaler_.transform(X))
            design = phi * self.t_res_[:, None]
            self.final_model_ = Ridge(alpha=1.0, fit_intercept=False).fit(design, self.y_res_)
        else:
            pseudo = self.y_res_ / np.where(np.abs(self.t_res_) < 1e-3, 1e-3, self.t_res_)
            self.final_model_ = LGBMRegressor(
                n_estimators=150, learning_rate=0.03, num_leaves=6,
                min_child_samples=60, subsample=0.8, subsample_freq=1,
                random_state=self.seed, verbose=-1,
            ).fit(X, pseudo, sample_weight=self.t_res_ ** 2)
        return self

    def effect_per_dollar(self, X):
        X = np.asarray(X, float)
        if self.final == "linear":
            phi = self.poly_.transform(self.scaler_.transform(X))
            return phi @ self.final_model_.coef_
        return self.final_model_.predict(X)

    def ite(self, X, dollars=10):
        """Estimated change in purchase probability from a `dollars` discount."""
        return self.effect_per_dollar(X) * dollars


def policy_report(name, score, true_ite, frac=0.4):
    """Treat the top `frac` of customers by predicted ITE; score by TRUE effect."""
    k = int(len(score) * frac)
    chosen = np.argsort(-score)[:k]
    gain = true_ite[chosen].sum()
    return gain, (true_ite[chosen] < -0.01).mean()


if __name__ == "__main__":
    df = pd.read_csv(ROOT / "data" / "customers_causal.csv")
    train, test = train_test_split(df, test_size=0.3, random_state=0)
    Xtr, Xte = train[FEATURES].values, test[FEATURES].values
    truth = test["true_ite_10"].values

    scores = {}

    # --- Baseline: predictive model, discount used as an ordinary feature -------
    clf = LGBMClassifier(n_estimators=200, learning_rate=0.05, verbose=-1, random_state=0)
    clf.fit(train[FEATURES + ["discount"]], train["purchase"])
    hi, lo = test[FEATURES].assign(discount=10), test[FEATURES].assign(discount=0)
    scores["Baseline (predictive)"] = (clf.predict_proba(hi)[:, 1] - clf.predict_proba(lo)[:, 1])

    # --- Our from-scratch Double ML ---------------------------------------------
    for final, label in [("linear", "Double ML (ours, linear final)"),
                         ("gbm", "Double ML (ours, GBM final)")]:
        m = DoubleML(final=final, seed=0).fit(Xtr, train["discount"], train["purchase"])
        scores[label] = m.ite(Xte, 10)

    # --- EconML reference implementations ---------------------------------------
    try:
        from econml.dml import CausalForestDML, LinearDML

        def lgbm():
            return LGBMRegressor(n_estimators=200, learning_rate=0.05, num_leaves=8,
                                 min_child_samples=30, random_state=0, verbose=-1)

        lin = LinearDML(model_y=lgbm(), model_t=lgbm(), cv=5, random_state=0,
                        featurizer=PolynomialFeatures(2, include_bias=False))
        lin.fit(train["purchase"].values, train["discount"].values, X=Xtr)
        scores["EconML LinearDML"] = lin.effect(Xte, T0=0, T1=10)

        cf = CausalForestDML(model_y=lgbm(), model_t=lgbm(), cv=5, n_estimators=300,
                             min_samples_leaf=20, random_state=0)
        cf.fit(train["purchase"].values, train["discount"].values, X=Xtr)
        scores["EconML CausalForestDML"] = cf.effect(Xte, T0=0, T1=10)
    except Exception as exc:
        print("EconML reference skipped:", exc)

    # --- Report ---------------------------------------------------------------------
    rng = np.random.default_rng(0)
    scores["Random targeting"] = rng.normal(size=len(test))
    oracle_gain, _ = policy_report("oracle", truth, truth)

    rows = []
    for name, s in scores.items():
        corr = np.corrcoef(s, truth)[0, 1] if name != "Random targeting" else np.nan
        rmse = np.sqrt(np.mean((s - truth) ** 2)) if name != "Random targeting" else np.nan
        gain, dogs = policy_report(name, s, truth)
        rows.append({"Model": name, "Mean est. ITE": s.mean() if name != "Random targeting" else np.nan,
                     "Corr with truth": corr, "RMSE": rmse,
                     "Gain, treat top 40%": gain, "% Sleeping Dogs treated": 100 * dogs})
    out = pd.DataFrame(rows).set_index("Model").round(3)

    print(f"Held-out customers: {len(test)} | true mean effect of $10: {truth.mean():+.3f}")
    print(f"Oracle gain (treat the true best 40%): {oracle_gain:.1f} extra purchases\n")
    print(out.to_string())
    print("\n'Gain' = extra purchases we would really cause by discounting the 40% the model "
          "ranks highest\n(measured with the TRUE effects; higher is better).")

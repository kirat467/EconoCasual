# EconoCasual - Data Analysis Report

## 1. Project Overview
EconoCasual analyzes customer purchasing behavior and studies how discounts and previous purchases relate to purchase decisions.

## 2. Dataset
The dataset is stored in customers.csv.

The analysis uses these customer attributes:
- Customer ID
- Previous Purchases
- Engagement
- Discount
- Purchase

## 3. Data Quality Checks
The following checks were performed:
- Displayed the first five rows.
- Checked the dataset dimensions.
- Identified the column names.
- Checked for missing values.
- Checked for duplicate rows.

## 4. Purchase Rate by Discount
A bar chart was created to compare purchase rates for customers who received discounts and those who did not.

The current results show:
- No discount: approximately 54% purchase rate.
- Discount offered: approximately 61% purchase rate.

## 5. Key Finding
In this dataset, the purchase rate is higher for customers offered discounts.

This indicates an association between discounts and customer purchasing behavior. It does not, by itself, prove that discounts caused the increase.

## 6. Purchase Rate by Previous Purchases
Purchase rates were also calculated for different numbers of previous purchases to explore the relationship between customer purchase history and purchasing behavior.

## 7. Tools Used
- Python
- Pandas
- Matplotlib

## 8. Conclusion
The analysis provides an initial understanding of customer purchasing behavior. These findings can support the next stage of EconoCasual: building a machine learning model to predict customer purchases.
## 9. Analysis Summary

- Analyzed customer purchasing behavior using Python and Pandas.
- Examined the relationship between discounts and purchase rates.
- Analyzed purchase rates based on customers' previous purchases.
- Visualized the results using Matplotlib charts.
- Prepared the initial analysis for the next stage of customer purchase prediction.
-Overall purchase rate calculated.
-Purchase rates analyzed by discount.
-Purchase rates analyzed by previous purchases.
-Customer engagement analysis.
-Three graphs generated.
-Preparation for customer purchase prediction.

## 10. Future Work

- Perform additional exploratory data analysis.
- Identify important features related to customer purchases.
- Prepare the dataset for machine learning.
- Develop and evaluate a customer purchase prediction model.

## 11. Customer Engagement Analysis

- Customer engagement was analyzed using Python and Pandas to understand its relationship with purchasing behavior.

- The average engagement value was calculated to understand overall customer engagement. Descriptive statistics were also generated to examine the distribution of engagement values.

- Purchase rates were calculated for different engagement groups using the mean of the purchase column. A bar chart was created to visualize the relationship between customer engagement and purchase behavior.

- The analysis helps identify differences in purchasing behavior across engagement groups.
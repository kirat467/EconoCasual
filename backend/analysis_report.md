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

## 12. Correlation Analysis

Correlation analysis was performed to understand the relationship between customer characteristics and purchase behavior.

The observed correlation values with purchase were:

- Previous Purchases: 0.30
- Customer Engagement: 0.18
- Discount: 0.05

### Key Findings

1. Previous purchases showed the strongest positive correlation with purchase behavior among these three variables.
2. Customer engagement showed a weaker positive correlation.
3. Discount showed a very weak positive correlation.

### Conclusion

Previous purchase history had the strongest observed relationship with purchase behavior in this dataset. These correlations do not establish causation.

## Customer Purchasing Behavior Analysis Summary

1. Objective

The objective is to analyze customer purchasing behavior and understand how customer engagement and previous purchases relate to purchase rates.

2. Data Analysis

Python and Pandas were used to examine the dataset, summarize customer purchasing behavior, and analyze relationships between numerical variables.

3. Customer Engagement

Customer engagement levels were compared with purchase behavior to identify patterns in customer activity and purchasing decisions.

4. Previous Purchases

Previous purchase history was examined to understand its relationship with customer purchasing behavior.

5. Data Visualization

Matplotlib was used to create graphs and a correlation heatmap to visualize relationships between numerical variables.

6. Conclusion

The analysis provides an initial understanding of customer purchasing behavior, engagement, and purchase history. These findings can help guide further analysis of customer engagement and purchasing patterns.

## Customer Analysis
1. Customer Segmentation

Customers were classified into four groups based on their previous purchase history and engagement levels:

- High-Value Customers
- Loyal Customers
- Highly Engaged Customers
- Customers Needing Attention

Purchase rates were calculated for each group to compare customer behavior.

2. Customer Attention Analysis

Customers were grouped into high, moderate, and low attention categories based on their previous purchases and engagement.

This analysis helps identify customer groups that may benefit from additional engagement efforts.

3. Customer Engagement Insights

Purchase rates were compared across different engagement levels. This analysis helps identify engagement levels associated with higher observed purchase rates.

4. Customer Insights Export

The analysis results were exported to "data/customer_insights.csv" for further examination and potential use by other project modules.

The original "customers.csv" dataset was kept unchanged.

5. Customer Loyalty Classification

Customers were classified as highly loyal, moderately loyal, or new or occasional customers using their previous purchase counts.

The distribution of these groups and their observed purchase rates were analyzed.

6. Limitations

The customer groups are based on simple, rule-based thresholds. The observed relationships do not prove causation, and the attention categories are not validated predictions of future purchases.

7. Future Improvements

- Integrate the analysis results with the frontend dashboard.
- Use machine learning to evaluate customer purchase predictions.
- Explore additional customer behavior features.
- Validate customer segmentation rules using more data.

## 8. Automated Customer Behavior Insights

An automated insights feature was added to summarize important customer behavior patterns.

### Key Metrics
- Overall customer purchase rate.
- Average number of previous purchases.
- Average customer engagement.
- Comparison between buyers and non-buyers.

### Business Insights
The analysis compares the purchasing history and engagement levels of buyers and non-buyers.

These comparisons help identify patterns that may support customer engagement strategies.

### Limitations
The results describe the current dataset and do not establish causation. The findings should be validated with additional data before making business decisions.## 8. Automated Customer Behavior Insights

An automated insights feature was added to summarize important customer behavior patterns.

### Key Metrics
- Overall customer purchase rate.
- Average number of previous purchases.
- Average customer engagement.
- Comparison between buyers and non-buyers.

### Business Insights
The analysis compares the purchasing history and engagement levels of buyers and non-buyers.

These comparisons help identify patterns that may support customer engagement strategies.

### Limitations
The results describe the current dataset and do not establish causation. The findings should be validated with additional data before making business decisions.

## 9. Data Validation

Data validation checks were added to assess the quality and consistency of the customer dataset.

The checks include:

- Missing values in dataset columns.
- Duplicate customer IDs.
- Invalid purchase values.
- Invalid discount values.
- Engagement values outside the expected range of 1 to 10.
- Negative previous purchase counts.

These checks help identify potential data quality issues before performing further analysis or training machine learning models.

The validation process checks the data without modifying the original dataset.

10. Data Quality Validation

Data quality checks were performed to verify the reliability of the customer dataset.

- Missing Values: Checked all columns for missing data.
- Duplicate Customer IDs: Checked for repeated customer IDs.
- Dataset Shape: Verified the number of rows and columns.
- Validation: The dataset was reviewed before using it for customer behavior analysis.

These checks help ensure that the dataset is suitable for the project's initial analysis.

Limitations of Current Analysis

- The analysis uses a synthetic customer dataset and may not represent real customer behavior.
- Correlation indicates association and does not prove causation.
- Purchase-rate comparisons describe observed patterns and do not guarantee future purchases.
- Further testing on real-world data is required before applying these findings in business decisions.
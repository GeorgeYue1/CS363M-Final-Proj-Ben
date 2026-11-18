1\. Describe the dataset. (ex: The number of microaneurysms found in a patient's eye and whether or not they have diabetic retinopathy; or Lending Tree loan data, including who defaulted and who paid off their loan.)

Based on feedback, we are switching from a single-year snapshot of 195 countries to a country-by-year panel dataset. We will combine the UNDP Human Development Index time series (our target) with the World Bank World Development Indicators (our features). Each record is one country in one year, with economic, demographic, health-infrastructure, and environmental indicators such as fertility rate, urbanization, access to electricity, and internet usage, along with that country's HDI for that year.

2\. How many records does the dataset have?

HDI is available for about 190 countries from 1990 to 2022, which gives roughly 6,000 country-year records. The final count will be somewhat lower after we drop or impute country-years with missing values.

3\. How many features does the dataset have? List or describe a few of them.

The World Development Indicators contain over 1,000 indicators, so we will select a subset of about 15–20 that have good coverage across countries and years.

Some of the features we plan to use include fertility rate, population growth, population density, urban population (%), access to electricity (%), internet users (%), CO2 emissions per capita, health expenditure (% of GDP), and agriculture (% of GDP).

We will deliberately exclude features that are components of HDI itself. HDI is calculated from life expectancy, mean and expected years of schooling, and GNI per capita, so using those (or near-duplicates such as GDP per capita or school enrollment rates) as inputs would let the model reconstruct the formula rather than learn anything meaningful. We will also compare results with and without closely related features such as infant mortality, which is strongly tied to life expectancy.

4\. What can you try to predict in this dataset? (ex: We can use the number of microaneurysms measured in the patient's eye to predict whether or not they have diabetic retinopathy; or We can try using the features, including age, income, home ownership status, etc, to predict whether or not someone will default on their loan.)

We are planning on predicting the Human Development Index (HDI). We can try using features that are not part of the HDI formula, including fertility rate, urbanization, access to electricity, internet usage, etc, to predict a country's HDI in a given year. Because the data spans multiple years, we can also look at how HDI changes over time and whether the model can predict HDI for later years when trained on earlier years.

5\. What kind of ML problem are you doing (e,g, classification, regression, clustering)? Is this a labeled dataset, appropriate for a supervised learning classification or regression problem? (Or will your project only focus on unsupervised learning?)

We are doing a regression problem. The dataset is labeled (each country-year has an HDI value), so it is appropriate for supervised learning.

6\. Provide a link to the dataset, if there is one. If you are getting your data from somewhere other than a link, where are you getting it from?

HDI time series (target): [https\://hdr.undp.org/data-center/documentation-and-downloads](https://hdr.undp.org/data-center/documentation-and-downloads) (also available through Our World in Data: [https\://ourworldindata.org/grapher/human-development-index](https://ourworldindata.org/grapher/human-development-index))

World Development Indicators (features): [https\://databank.worldbank.org/source/world-development-indicators](https://databank.worldbank.org/source/world-development-indicators)

7\. Briefly describe a plan of things you plan on doing (no need to have all details right now, but if you know your data is messy you should have a plan on how you will clean and preprocess, and also an idea of what algorithms you want to try).

- **Merge and clean:** Join the HDI and World Bank data on country code and year. Drop regional and income-group aggregates (e.g., "Sub-Saharan Africa", "High income") so that only individual countries remain. Remove indicators with heavy missingness, and impute the remaining gaps (for example, interpolation within each country across years).
- **Feature selection:** Exclude HDI components and their near-duplicates as described above, and check correlations between features to spot any other leakage.
- **Preprocessing:** Scale features using z-score normalization, and log-transform skewed features such as population density and CO2 per capita.
- **Train/test split:** Since rows from the same country in different years are highly correlated, a random split would overstate performance. We will split by country (grouped cross-validation) and also try a time-based split (train on earlier years, test on later years).
- **Models:** Start with multiple linear regression as a baseline, then evaluate polynomial regression and regularized regression (ridge/lasso). If time permits, we will compare these against a tree-based model such as a random forest.
- **Evaluation:** Compare models using RMSE and R², and look at which features matter most and how prediction errors vary across regions and over time.

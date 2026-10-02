# Project Report: Wholesale Customers Clustering

## 1. Problem Framing & Choice of Clustering Methods

**Problem:** The goal of this project is to segment **440 wholesale customers** based on their annual spending across six product categories: **Fresh, Milk, Grocery, Frozen, Detergents_Paper and Delicassen**.

The main idea is simple: customers who purchase similar products and have similar spending patterns should fall into the same group. These groups can then be used for targeted marketing, inventory planning and pricing decisions.

**Why clustering?** This is an **unsupervised learning** problem because we do not have a predefined customer segment label. The algorithm has to find the natural groups from the spending data itself.

**Methods used:**
- **K-Means:** Divides customers into a fixed number of clusters based on distance from cluster centers. It is simple and easy to interpret.
- **Hierarchical / Agglomerative Clustering:** Builds clusters step by step and gives a dendrogram to understand how observations/groups are merged.
- **DBSCAN:** Groups points based on density and can also identify points that do not belong to a dense group as noise.

The clustering was performed only on the six spending features. **Channel and Region were not used as input features**, so that the model would discover the customer groups from purchasing behaviour instead of simply reproducing those existing labels.

---

## 2. Data Understanding & EDA

The dataset contains **440 rows and 8 columns**. The six spending columns are the main features used for clustering, while Channel and Region are used later for interpretation.

There are **no missing values** in the dataset.

### Key EDA Insights

1. **Spending data is highly right-skewed:** All six spending features have skewness above 2, ranging approximately from **2.56 to 11.15**. This means most customers spend relatively less, while a smaller number of customers have very high spending.

2. **Outliers are present:** Box plots show many high-value observations, especially in the spending features. These values can strongly affect distance-based clustering.

3. **Strong correlation:** Grocery and Detergents_Paper have a very strong correlation of about **0.92**. Milk is also correlated with both. This suggests a common household/retail-staples purchasing pattern.

4. **Fresh and Frozen behave differently:** They are comparatively more independent from the Grocery–Milk–Detergents group.

5. **Channel already shows a natural pattern:** The pair plot suggests that HoReCa and Retail customers have different spending behaviour. This pattern is later reflected in the clusters.

---

## 3. Preprocessing

### 3.1 Log Transformation

Because the spending features are heavily right-skewed, `log1p()` transformation was applied to all six spending columns.

**Why?** A few extremely high-spending customers can dominate distance calculations. Log transformation compresses very large values and makes the distribution less distorted.

After transformation, the skewness was substantially reduced for most features.

### 3.2 Feature Scaling

After the log transformation, **StandardScaler** was applied.

The resulting feature matrix has a shape of **440 × 6**.

Standardization converts each feature approximately to:
- Mean = 0
- Standard deviation = 1

This is important because K-Means, DBSCAN and other clustering methods use distances. Without scaling, a feature with larger numerical values can have more influence than the others.

---

## 4. Clustering & Evaluation

### 4.1 K-Means Clustering

K-Means was tested for **k = 2 to 10**.

The results showed:
- **k = 2:** Silhouette Score = **0.2903**
- **k = 3:** Silhouette Score = **0.2594**

The Elbow plot showed the main bend around **k = 2–3**. Since k=2 gave the better silhouette score and produced a clearer business interpretation, **K-Means with k=2** was selected as the primary clustering result.

For k=2, the cluster sizes are:
- Cluster 0: **252 customers**
- Cluster 1: **188 customers**

### 4.2 Hierarchical / Agglomerative Clustering

Agglomerative clustering with **Ward linkage** was also tested.

- k = 2 → Silhouette Score = **0.2585**
- k = 3 → Silhouette Score = **0.2547**

The dendrogram also helped visualize the hierarchical structure of the customers.

### 4.3 DBSCAN

DBSCAN was tested using different values of `eps` and `min_samples`.

The best tested configuration was:
- **eps = 1.5**
- **min_samples = 3**
- **Clusters = 2**
- **Noise points = 35**
- **Silhouette Score = 0.2989**

DBSCAN achieved the highest raw silhouette score among the tested methods, but it marked 35 customers as noise. For the final business interpretation, K-Means k=2 was used because it gives a clean and directly interpretable segmentation of the full customer base.

### Method Comparison

| Method | Silhouette Score |
|---|---:|
| DBSCAN (eps=1.5, min_samples=3) | 0.2989 |
| K-Means (k=2) | 0.2903 |
| K-Means (k=3) | 0.2594 |
| Agglomerative (k=2) | 0.2585 |
| Agglomerative (k=3) | 0.2547 |

---

## 5. Final Cluster Profiling

The final business interpretation uses **K-Means with k=2**.

| Attribute | Cluster 0 — Fresh-focused / HoReCa | Cluster 1 — Grocery-focused / Retail |
|---|---|---|
| **Customers** | 252 | 188 |
| **Main spending** | Fresh, Frozen, Delicassen | Grocery, Milk, Detergents_Paper |
| **Channel pattern** | 96.8% Channel 1 | 71.3% Channel 2 |
| **Buying behaviour** | Higher spending on fresh and frozen products | Higher spending on household/retail staples |
| **Business interpretation** | Likely hotels, restaurants and cafes | Likely retail customers |

### Cluster 0 — Fresh-focused Customers

Cluster 0 has higher average spending on **Fresh, Frozen and Delicassen** and much lower spending on Grocery, Milk and Detergents_Paper.

The cluster is strongly associated with **Channel 1**, with about **96.8%** of its customers belonging to that channel. This matches the expected HoReCa purchasing pattern.

**Business action:** Focus on bulk discounts for fresh and frozen products and reliable delivery, especially for perishable goods.

### Cluster 1 — Grocery-focused Customers

Cluster 1 has much higher average spending on **Grocery, Milk and Detergents_Paper** and lower spending on Fresh and Frozen.

About **71.3%** of this cluster belongs to **Channel 2**, which matches the retail-oriented purchasing pattern.

**Business action:** Use grocery and detergent offers, product bundles and loyalty programs for repeat customers.

---

## 6. Visualizations & What They Tell Us

- **Distribution plots:** Showed the strong right skew in spending data.
- **Box plots:** Helped identify high-value outliers.
- **Correlation heatmap:** Showed the strong relationship between Grocery, Detergents_Paper and Milk.
- **Pair plot:** Showed different purchasing patterns across channels.
- **Elbow plot:** Helped identify the useful range for the number of clusters.
- **Silhouette score:** Helped compare the quality of different clustering choices.
- **Dendrogram:** Showed how customers/groups are progressively merged in hierarchical clustering.
- **Centroid heatmap:** Made the spending differences between the two K-Means clusters easier to understand.
- **PCA:** Reduced the six-dimensional spending data to two dimensions for visualization. The first two components explain **71.27%** of the variance.
- **t-SNE:** Provided another two-dimensional view of the customer structure and cluster separation.
- **Side-by-side PCA plots:** Compared K-Means, Agglomerative and DBSCAN results visually.

---

## 7. Final Conclusion

The project successfully identified **two major customer segments** from wholesale purchasing behaviour.

**Final approach:**
1. Load and inspect the wholesale customer data.
2. Perform EDA to understand distributions, correlations and outliers.
3. Apply log transformation to reduce heavy skewness.
4. Standardize the spending features.
5. Test K-Means, Agglomerative Clustering and DBSCAN.
6. Compare the methods using silhouette scores and visualizations.
7. Use **K-Means k=2** as the primary business segmentation.
8. Profile the clusters using original spending values, Channel and Region.

The main result is a clear distinction between **Fresh/Frozen-focused HoReCa customers** and **Grocery/Milk/Detergents-focused Retail customers**.

These segments can be used for **targeted marketing, inventory planning, bulk discounts, pricing and customer retention**.

---

## 8. Basic Terminology — In Simple Words

| Term | Simple meaning |
|---|---|
| **Clustering** | Grouping similar data points together without predefined labels. |
| **Unsupervised Learning** | Learning patterns from data when the correct output/label is not already given. |
| **Feature** | An input column used to describe each customer. Here, spending categories are the main features. |
| **Skewness** | Shows whether a distribution is pulled more toward one side. High positive skew means a long right tail. |
| **Outlier** | A value that is unusually far from most other observations. |
| **Log Transformation** | Compresses large values and reduces the effect of extreme values. |
| **Standardization** | Converts features to a common scale with mean 0 and standard deviation 1. |
| **Distance** | Measures how different two data points are. Clustering algorithms use distance to decide which points are similar. |
| **K-Means** | Creates K groups and assigns each point to the nearest cluster center. |
| **Centroid** | The center/representative point of a K-Means cluster. |
| **Inertia** | Measures how close points are to their assigned K-Means centroids. Lower is better, but it generally decreases as K increases. |
| **Elbow Method** | Looks for the point where increasing the number of clusters gives much less improvement. |
| **Silhouette Score** | Measures how well each point fits its own cluster compared with other clusters. Higher is generally better. |
| **Agglomerative Clustering** | Starts with individual points and repeatedly merges similar groups. |
| **Dendrogram** | A tree-like diagram showing how groups are merged in hierarchical clustering. |
| **Ward Linkage** | A hierarchical clustering method that chooses merges that keep within-cluster variation small. |
| **DBSCAN** | A density-based clustering algorithm that finds dense groups and can mark isolated points as noise. |
| **eps** | In DBSCAN, the distance around a point used to search for nearby points. |
| **min_samples** | Minimum number of nearby points needed to consider an area dense. |
| **Noise** | Points that DBSCAN could not assign to a dense cluster. |
| **Correlation** | Measures how two variables move together. A value close to +1 means a strong positive relationship. |
| **PCA** | Reduces many dimensions into fewer components while retaining as much variance as possible. |
| **Variance** | Measures how much the data values differ from their average. |
| **t-SNE** | A visualization technique that maps high-dimensional data into lower dimensions while trying to preserve local relationships. |
| **Cluster Profiling** | Studying the characteristics of each cluster after clustering to understand what the groups actually represent. |

**In one line:** We took customer spending data → understood the data → reduced skew → scaled the features → tested multiple clustering methods → selected K-Means k=2 for the final business segmentation → profiled the two customer types.

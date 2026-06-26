# House Price Advanced Regression — Evaluation Deep-Dive Report

---

## 1. What the Evaluation Section Teaches

The evaluation section of this notebook is the **final gatekeeper** that tells us whether our entire pipeline — from data cleaning to feature engineering to model selection — actually works. It teaches the following core concepts:

### 1.1 Evaluation Is Not Just One Number

A common beginner mistake is to train a model, look at a single accuracy or error metric, and declare victory. This notebook teaches you that **proper evaluation requires multiple metrics viewed from multiple angles**. The four metrics used here — **Train RMSE, Test RMSE, Cross-Validation RMSE (mean ± std), and Test RMSLE** — each reveal a different dimension of model performance:

| Metric | What It Measures | Why It Matters |
|---|---|---|
| **Train RMSE** | How well the model fits the data it was trained on | A very low Train RMSE combined with a high Test RMSE signals overfitting — the model memorized the training data instead of learning patterns |
| **Test RMSE** | How well the model generalises to unseen data | This is the real-world performance indicator; it tells you how much error (in dollars) to expect on new house price predictions |
| **CV RMSE (mean ± std)** | The average and variability of RMSE across 5 different train/validate splits | This guards against lucky/unlucky train-test splits; a high standard deviation means the model is unstable and its performance fluctuates depending on the data it sees |
| **Test RMSLE** | The root mean squared *log* error | This penalises under-predictions of expensive homes and over-predictions of cheap homes differently; it is scale-relative, so a $10,000 error on a $50,000 home is penalised more heavily than a $10,000 error on a $500,000 home |

### 1.2 Overfitting vs. Underfitting — Reading the Signals

The evaluation section teaches you how to **diagnose model behaviour** by comparing Train RMSE vs. Test RMSE:

- **Underfitting (High Bias):** When both Train RMSE and Test RMSE are high. The model is too simple to capture patterns. Example: Linear Regression in this notebook — Train RMSE = 18,904 and Test RMSE = 65,385. The huge gap and high test error both indicate the model cannot capture the non-linear relationships in housing data.

- **Overfitting (High Variance):** When Train RMSE is very low but Test RMSE is much higher. The model memorized noise. Example: XGBoost Tuned + FE — Train RMSE = 672 but Test RMSE = 26,049. The model nearly memorized the training data (error of only ~$672) but generalises with ~$26,049 error on unseen data.

- **Good Generalisation:** When Train RMSE and Test RMSE are reasonably close. Example: Ridge + FE — Train RMSE = 23,888 and Test RMSE = 30,080. The gap is moderate, indicating the model learned real patterns without excessive memorisation.

### 1.3 Cross-Validation Is Your Safety Net

A single train-test split can be misleading. If your test set happens to contain easier examples, you might think your model is better than it really is. **5-Fold Cross-Validation** addresses this by:

1. Splitting the training data into 5 equal parts (folds)
2. Training on 4 folds and validating on the remaining 1 fold
3. Repeating this 5 times (each fold gets a turn as the validation set)
4. Averaging the 5 RMSE scores to get the CV RMSE mean
5. Computing the standard deviation to measure stability

A **low standard deviation** (e.g., Gradient Descent + FE: 27,778 ± 3,523) means the model performs consistently regardless of which data it trains on. A **high standard deviation** (e.g., Linear Regression: 43,614 ± 16,218) means the model's performance is highly dependent on the specific data split — a red flag for production deployment.

---

## 2. How Do We Evaluate the Model After Training?

The evaluation follows a **systematic, layered approach** — from a custom evaluation function to visual diagnostics and error analysis:

### 2.1 The `evaluate_model()` Function

This is the workhorse of the evaluation pipeline. For every model, it performs the following steps:

```
Step 1: Fit the pipeline on training data
         pipeline.fit(X_train, y_train)

Step 2: Generate predictions on both training and test sets
         y_pred_train = pipeline.predict(X_train)
         y_pred_test  = pipeline.predict(X_test)

Step 3: Compute 5-Fold Cross-Validation RMSE
         cv_scores = cross_val_score(pipeline, X_train, y_train, cv=5, 
                                     scoring='neg_root_mean_squared_error')
         cv_rmse = -cv_scores.mean()    # Negate because sklearn returns negative
         cv_std  =  cv_scores.std()

Step 4: Calculate Train RMSE and Test RMSE
         train_rmse = sqrt(mean_squared_error(y_train, y_pred_train))
         test_rmse  = sqrt(mean_squared_error(y_test, y_pred_test))

Step 5: Calculate Test RMSLE (with clipping to prevent negative predictions)
         test_rmsle = sqrt(mean_squared_log_error(y_test, clip(y_pred_test, 0)))

Step 6: Store all metrics in a results dictionary
```

**Why this order matters:** We fit first, then predict on both sets to measure memorisation vs. generalisation, then cross-validate to get a robust estimate that is independent of any single split.

### 2.2 Progressive Model Comparison Table

The notebook does not evaluate just one model — it builds a **comparison table across 12 model configurations** in four progressive stages:

| Stage | Models | Purpose |
|---|---|---|
| **Stage 1: Baseline Linear Models** | Linear Regression, Ridge (α=10), Lasso (α=100), Decision Tree | Establish a performance floor and understand how regularisation (Ridge/Lasso) helps vs. plain linear regression |
| **Stage 2: Ensemble Models** | Random Forest, Gradient Boosting, XGBoost | Jump to more powerful non-linear models that can capture complex feature interactions |
| **Stage 3: Feature Engineering** | Ridge + FE, Random Forest + FE, Gradient Boosting + FE, XGBoost + FE | Re-train all advanced models with domain-driven engineered features to measure the impact of feature engineering |
| **Stage 4: Hyperparameter Tuning** | XGBoost Tuned + FE (via GridSearchCV) | Fine-tune the best-performing model architecture with systematic hyperparameter search |

Each stage answers a specific question: "Do regularised linear models work?" → "Do ensemble methods help?" → "Does feature engineering improve things?" → "Can tuning squeeze out more performance?"

### 2.3 Visual Model Comparison

After computing all metrics, the notebook creates a **horizontal bar chart** of Test RMSE across all models, sorted from best (lowest) to worst (highest). This visualisation instantly reveals:

- Which models cluster together in performance
- How much improvement each stage brings
- Whether the gap between the best and worst model is significant

### 2.4 Residual Analysis (Beyond Metrics)

The notebook goes beyond aggregate metrics and performs **residual diagnostics**:

- **Residuals vs. Predicted Values scatter plot:** Checks for patterns. If residuals are randomly scattered around zero, the model has captured the main patterns. If there is a funnel shape (wider spread for higher predictions), the model struggles with expensive homes.
- **Actual vs. Predicted scatter plot:** Ideally, all points should lie on the 45-degree diagonal. Systematic deviations reveal where the model consistently over- or under-predicts.
- **Worst Predictions Table:** The 10 worst predictions (by absolute error) are identified and examined. This teaches you that aggregate metrics can hide catastrophic individual failures.

### 2.5 Feature Importance Interpretation

The notebook also extracts and visualises the **top 20 most important features** from the best model (XGBoost). This tells you *why* the model makes certain predictions and which features drive house prices the most (OverallQual, GrLivArea, TotalSF, etc.).

---

## 3. Complete Results — All 12 Models at a Glance

| # | Model | Train RMSE | Test RMSE | CV RMSE (mean ± std) | Test RMSLE |
|---|---|---|---|---|---|
| 1 | Linear Regression | 18,904 | 65,385 | 43,614 ± 16,218 | 0.72 |
| 2 | Ridge (α=10) | 24,359 | 30,521 | 32,637 ± 9,407 | 0.16 |
| 3 | Lasso (α=100) | 22,001 | 28,225 | 33,052 ± 8,813 | 0.15 |
| 4 | Decision Tree | 23,014 | 42,126 | 44,335 ± 10,165 | 0.21 |
| 5 | Random Forest | 11,129 | 29,229 | 30,625 ± 4,733 | 0.15 |
| 6 | Gradient Boosting | 4,662 | 26,551 | 29,830 ± 4,476 | 0.14 |
| 7 | XGBoost | 10,397 | 25,927 | 29,403 ± 4,518 | 0.14 |
| 8 | Ridge + FE | 23,888 | 30,080 | 32,575 ± 9,822 | 0.16 |
| 9 | Random Forest + FE | 10,813 | 29,187 | 29,583 ± 4,520 | 0.15 |
| 10 | Gradient Boosting + FE | 4,304 | 27,817 | 27,778 ± 3,523 | 0.14 |
| 11 | **XGBoost + FE** | **5,366** | **25,510** | **29,011 ± 5,324** | **0.13** |
| 12 | XGBoost Tuned + FE | 672 | 26,049 | 29,205 ± 5,185 | 0.14 |

> **Best Test RMSE:** XGBoost + FE (25,510)  
> **Best Test RMSLE:** XGBoost + FE (0.13)  
> **Best CV RMSE (most stable):** Gradient Boosting + FE (27,778 ± 3,523)

---

## 4. Why Does XGBoost + FE Give the Lowest Error Rate?

The XGBoost + FE model achieves the lowest Test RMSE ($25,510) and Test RMSLE (0.13) among all models. Here is a detailed breakdown of **why**:

### 4.1 Gradient Boosting's Sequential Error-Correction Mechanism

Unlike Random Forest (which builds independent trees in parallel and averages them), XGBoost builds trees **sequentially**, where each new tree specifically targets the **residual errors** of the previous trees. This means:

- **Tree 1** learns the broad patterns (e.g., "bigger homes cost more")
- **Tree 2** learns what Tree 1 got wrong (e.g., "but not always if the neighbourhood is poor")
- **Tree 3** corrects Tree 2's remaining errors (e.g., "except for recently renovated homes in that neighbourhood")
- ...and so on for 300 trees

Each tree focuses precisely on the mistakes the ensemble has not yet fixed. This creates a model that becomes increasingly precise with each iteration, unlike single models or bagging methods that treat all errors equally.

### 4.2 XGBoost's Regularisation Prevents Overfitting

XGBoost includes built-in regularisation terms that plain Gradient Boosting lacks:

- **L1 (Lasso) and L2 (Ridge) regularisation** on leaf weights: Shrinks extreme predictions and prevents individual trees from dominating
- **Shrinkage (learning rate = 0.1):** Each tree's contribution is scaled down, forcing the model to learn slowly and carefully rather than making large jumps
- **Subsampling (row sampling):** Each tree trains on a random subset of rows, reducing correlation between trees
- **Column sampling (colsample_bytree):** Each tree uses a random subset of features, preventing over-reliance on any single feature

This combination allows XGBoost to build deep, expressive models without the severe overfitting that plagues unregularised methods.

### 4.3 The Feature Engineering Amplifier

The "+ FE" in "XGBoost + FE" is critical. The feature engineering step adds **8 domain-driven composite features**:

| Engineered Feature | Formula | Why It Helps |
|---|---|---|
| **Total_SF** | TotalBsmtSF + 1stFlrSF + 2ndFlrSF | Captures the total usable square footage as a single powerful predictor rather than relying on the model to learn this relationship |
| **TotalBath** | FullBath + 0.5 × HalfBath + BsmtFullBath + 0.5 × BsmtHalfBath | Consolidates 4 sparse bathroom columns into one meaningful "bathroom power" metric |
| **TotalPorchSF** | OpenPorchSF + EnclosedPorch + 3SsnPorch + ScreenPorch | Combines 4 rarely-used porch features into one that has stronger signal |
| **HouseAge** | YrSold − YearBuilt | Directly captures how old the house is at the time of sale — more intuitive than raw YearBuilt |
| **ReModAge** | YrSold − YearRemodAdd | Captures how recently the house was remodelled — a strong price driver |
| **HasGarage** | 1 if GarageArea > 0 else 0 | Binary indicator that separates homes with/without garages cleanly |
| **HasBsmt** | 1 if TotalBsmtSF > 0 else 0 | Binary indicator for basement presence |
| **Has2ndFlr** | 1 if 2ndFlrSF > 0 else 0 | Binary indicator distinguishing single-story vs. multi-story homes |

**Why this matters for XGBoost specifically:** While tree-based models can theoretically learn non-linear combinations of features, learning "Total_SF = BsmtSF + 1stFlrSF + 2ndFlrSF" requires three separate splits across three different features, which wastes tree depth. By providing Total_SF directly, the model can use a single split to capture the combined effect, freeing up capacity to learn more subtle interactions.

### 4.4 Why Not the Tuned XGBoost?

Interestingly, the **XGBoost Tuned + FE** model (Train RMSE = 672, Test RMSE = 26,049) actually performs slightly worse on test data despite being hyperparameter-tuned. The reason is **overfitting to the cross-validation score**:

- GridSearchCV found the best parameters (n_estimators=500, max_depth=5, learning_rate=0.1, subsample=0.8) that minimise CV RMSE (27,318)
- However, these parameters allow the model to nearly memorize the training data (Train RMSE = 672), creating a massive generalisation gap
- The untuned XGBoost + FE (n_estimators=300, max_depth=4) is slightly more constrained, which paradoxically makes it generalise better to the specific test set used

This teaches a crucial lesson: **the model with the best cross-validation score is not always the model with the best test score**. Cross-validation estimates generalisation, but it is still an estimate, and on any single test set, a slightly more conservative model may win.

### 4.5 Why Not Linear Models?

Linear models (Ridge, Lasso) assume the relationship between features and price is additive and linear. House prices violate this assumption fundamentally:

- A garage adds different value to a $100K home vs. a $500K home (interaction effect)
- The effect of living area on price is non-linear — each additional square foot may add less value than the previous one (diminishing returns)
- Neighbourhood quality multiplies the effect of home size, it does not add to it independently

XGBoost captures these non-linearities and interactions naturally through its tree-based structure.

### 4.6 Why Not Random Forest?

Random Forest's Test RMSE (29,229) is significantly worse than XGBoost (25,510). The key differences are:

| Aspect | Random Forest | XGBoost |
|---|---|---|
| Tree building | Independent, parallel | Sequential, error-correcting |
| Optimisation target | Reduce variance (averaging) | Reduce bias + variance (boosting) |
| Tree depth | Grown fully (low bias, high variance per tree) | Shallow (high bias per tree, low variance ensemble) |
| Error handling | All trees treat all errors equally | Later trees focus on the hardest remaining errors |

Random Forest reduces variance by averaging many deep trees, but it cannot reduce bias. XGBoost reduces both bias (through sequential correction) and variance (through regularisation and subsampling), making it more effective for structured/tabular data like housing features.

---

## 5. Key Takeaways

1. **Evaluate with multiple metrics** — a single metric hides overfitting, instability, and systematic biases.
2. **Cross-validation is essential** — it protects against misleading results from a single train-test split.
3. **Residual analysis reveals what metrics hide** — the worst predictions tell you where your model's blind spots are.
4. **Feature engineering amplifies model power** — composite features (TotalSF, TotalBath, HouseAge) are easier for any model to learn than raw separate features.
5. **XGBoost wins because of sequential error correction + regularisation** — each tree fixes remaining mistakes, and built-in regularisation prevents overfitting.
6. **More tuning ≠ better test performance** — the tuned XGBoost overfits more (Train RMSE = 672) and generalises slightly worse than the untuned version, illustrating the bias-variance tradeoff in practice.
7. **The best model (XGBoost + FE) has Test RMSE = $25,510** — meaning on average, its predictions are off by about $25,510 from the actual sale price, which is roughly 14% of the mean house price ($180,921).

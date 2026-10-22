# CAT 2 presentation guide

**AI Application: Classification. Algorithm/Approach: Logistic Regression.** Open `LogisticRegression_Base.ipynb` and be able to explain every output. The existing weighted matcher is the **Rule-Based Baseline**, not the trained model.

| Question the lecturer may ask | Short explanation |
| --- | --- |
| What is classified? | One lost-report/found-report pair at a time. |
| What are the classes? | `1` means labelled match; `0` means labelled non-match in this experiment. |
| What happens to `plausible`? | It is mapped to 0 as a difficult negative for CAT 2, but is not independently verified as a different item; we also evaluate with plausible rows excluded. |
| Why Logistic Regression? | A simple binary classifier that learns weights for numeric features and returns a score. It is a base model, not a final production choice. |
| Why are labelled pairs needed? | A supervised classifier needs examples with known targets. Delhi Metro has found items but no paired lost reports or confirmed matches. |
| What is feature engineering? | Turning two reports into numbers, such as description overlap, matching category, conflicting colour or time proximity. |
| What does description similarity mean? | Shared normalized words divided by distinct normalized words in both descriptions (Jaccard overlap). |
| What does category match mean? | It is 1 only when both categories are present and normalized to the same value; missing values give match=0 and conflict=0. |
| What are X and y? | `X` is the numeric pair-feature table; `y` is the binary target column. |
| What is training? | Fit the scaler and Logistic Regression coefficients using labelled development pairs only. |
| What is validation? | Check performance on development groups the model did not train on. |
| What is data leakage? | Information from validation/test cases reaching training. We keep all pairs for a lost report in one group and fit the scaler inside each fold. |
| Why group by lost report? | The same lost description occurs in several candidate pairs. Splitting those pairs across train and validation would make evaluation too easy. |
| What is precision? | Among pairs predicted as matches, the share labelled match. |
| What is recall? | Among labelled matches, the share predicted as match. |
| What is F1? | A balance of precision and recall. |
| What is a confusion matrix? | Counts of correct and incorrect predictions for the two classes. Rows are actual 0/1; columns are predicted 0/1. |
| What is a false positive? | A class-0 pair predicted as a match. This can waste staff time or expose a sensitive candidate. |
| What is a false negative? | A labelled match missed by the classifier. This can hide a useful candidate. |
| What are the limits? | Only 32 designed pairs, eight held-out test pairs, labels without independent review, and no real campus field test. The old rule weights may have been shaped by this synthetic set. |
| Why human verification? | Similar reports do not prove that a claimant owns an item. Private ownership evidence belongs in a controlled staff process. |
| Where does CLIP fit? | Later, frozen image/text embeddings may provide extra similarity features after consented same-item image pairs exist. CLIP is not the CAT 2 classifier. |

The notebook calculates four EDA observations from the files. Each group member should explain **why** a cleaning choice or feature exists and identify at least one model error. Do not memorise numbers without opening the executed output.

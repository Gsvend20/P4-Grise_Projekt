from os import listdir
import cv2
import numpy as np
#import sklearn as skl
#import matplotlib as plt
import matplotlib.pyplot as plt
from matplotlib.colors import ListedColormap
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import StandardScaler
from sklearn.neural_network import MLPClassifier
from sklearn.neighbors import KNeighborsClassifier
from sklearn.svm import SVC
from sklearn.gaussian_process import GaussianProcessClassifier
from sklearn.gaussian_process.kernels import RBF
from sklearn.tree import DecisionTreeClassifier
from sklearn.ensemble import RandomForestClassifier, AdaBoostClassifier
from sklearn.naive_bayes import GaussianNB
from sklearn.discriminant_analysis import QuadraticDiscriminantAnalysis

class FeatureSpace:
    def __init__(self):
        self.centerX = []
        self.centerY = []
        self.convex_ratio_perimeter = []
        self.hierachy_Bool = []
        self.compactness = []
        self.elongation = []
        self.ferets_angle = []
        self.ferets = []
        self.thinness = []

    def createFeatures(self, contours, hierarchy):
        hierarchy = hierarchy[0]  # Unpacking [[[[[[[hierarchy]]]]]]]
        largest_area = 0
        # TODO: only gets the biggest one for now
        for k in range(len(contours)):
            area = cv2.contourArea(contours[k])
            if area > largest_area:
                largest_area = area
                cnt = contours[k]
                hrc = np.array(hierarchy[k][2] != -1)

        # Check for holes
        self.hierachy_Bool.append(int(hrc))

        # Center of mass
        M = cv2.moments(cnt)
        self.centerX.append(int(M['m10'] / M['m00']))
        self.centerY.append(int(M['m01'] / M['m00']))

        #
        perimeter = cv2.arcLength(cnt, True)
        hull = cv2.convexHull(cnt)
        hullperimeter = cv2.arcLength(hull, True)
        self.convex_ratio_perimeter.append(int(hullperimeter/perimeter))

        # Compactness
        self.compactness.append(int(largest_area/(img.shape[0]*img.shape[1])))

        # Elongation of min area rect
        (x_elon, y_elon), (width_elon, height_elon), angle = cv2.minAreaRect(cnt)
        self.elongation.append(int(min(width_elon, height_elon) / max(width_elon, height_elon)))

        # Longest internal line and its angle
        self.ferets_angle.append(angle)
        self.ferets.append(max(width_elon, height_elon))

        # Thinness TODO: Needs normalisation
        self.thinness.append(perimeter / largest_area)


def plot_features(dataset_1, dataset_2, figure_number):
    h = 0.02  # step size in the mesh
    datasets = [dataset_1, dataset_2]

    names = [
        "Nearest Neighbors",
        "Linear SVM",
        "RBF SVM",
        "Gaussian Process",
        "Decision Tree",
        "Random Forest",
        "Neural Net",
        "AdaBoost",
        "Naive Bayes",
        "QDA",
    ]

    classifiers = [
        KNeighborsClassifier(3),
        SVC(kernel="linear", C=0.025),
        SVC(gamma=2, C=1),
        GaussianProcessClassifier(1.0 * RBF(1.0)),
        DecisionTreeClassifier(max_depth=5),
        RandomForestClassifier(max_depth=5, n_estimators=10, max_features=1),
        MLPClassifier(alpha=1, max_iter=1000),
        AdaBoostClassifier(),
        GaussianNB(),
        QuadraticDiscriminantAnalysis(),
    ]

    figure = plt.figure(figsize=(27, 9))
    i = 1
    # iterate over datasets
    for ds_cnt, ds in enumerate(datasets):
        # preprocess dataset, split into training and test part
        X, y = ds
        X = StandardScaler().fit_transform(X)
        X_train, X_test, y_train, y_test = train_test_split(
            X, y, test_size=0.4, random_state=42
        )

        x_min, x_max = X[:, 0].min() - 0.5, X[:, 0].max() + 0.5
        y_min, y_max = X[:, 1].min() - 0.5, X[:, 1].max() + 0.5
        xx, yy = np.meshgrid(np.arange(x_min, x_max, h), np.arange(y_min, y_max, h))

        # just plot the dataset first
        cm = plt.cm.RdBu
        cm_bright = ListedColormap(["#FF0000", "#0000FF"])
        ax = plt.subplot(len(datasets), len(classifiers) + 1, i)
        if ds_cnt == 0:
            ax.set_title("Input data")
        # Plot the training points
        ax.scatter(X_train[:, 0], X_train[:, 1], c=y_train, cmap=cm_bright, edgecolors="k")
        # Plot the testing points
        ax.scatter(
            X_test[:, 0], X_test[:, 1], c=y_test, cmap=cm_bright, alpha=0.6, edgecolors="k"
        )
        ax.set_xlim(xx.min(), xx.max())
        ax.set_ylim(yy.min(), yy.max())
        ax.set_xticks(())
        ax.set_yticks(())
        i += 1

        # iterate over classifiers
        for name, clf in zip(names, classifiers):
            ax = plt.subplot(len(datasets), len(classifiers) + 1, i)
            clf.fit(X_train, y_train)
            score = clf.score(X_test, y_test)

            # Plot the decision boundary. For that, we will assign a color to each
            # point in the mesh [x_min, x_max]x[y_min, y_max].
            if hasattr(clf, "decision_function"):
                Z = clf.decision_function(np.c_[xx.ravel(), yy.ravel()])
            else:
                Z = clf.predict_proba(np.c_[xx.ravel(), yy.ravel()])[:, 1]

            # Put the result into a color plot
            Z = Z.reshape(xx.shape)
            ax.contourf(xx, yy, Z, cmap=cm, alpha=0.8)

            # Plot the training points
            ax.scatter(
                X_train[:, 0], X_train[:, 1], c=y_train, cmap=cm_bright, edgecolors="k"
            )
            # Plot the testing points
            ax.scatter(
                X_test[:, 0],
                X_test[:, 1],
                c=y_test,
                cmap=cm_bright,
                edgecolors="k",
                alpha=0.6,
            )

            ax.set_xlim(xx.min(), xx.max())
            ax.set_ylim(yy.min(), yy.max())
            ax.set_xticks(())
            ax.set_yticks(())
            if ds_cnt == 0:
                ax.set_title(name)
            ax.text(
                xx.max() - 0.3,
                yy.min() + 0.3,
                ("%.2f" % score).lstrip("0"),
                size=15,
                horizontalalignment="right",
            )
            i += 1

    plt.tight_layout()
    plt.show()
    return

sand = FeatureSpace()
types = [15, 55, 120, 150]
folder = "Sandtraindata"
for i in types:
    mask = listdir(f"{folder}/{i}/bgr/rgbMasks")
    for j in mask:
        checkpng = j.find("png")
        if checkpng >= 1:
            img = cv2.imread(f"{folder}/{i}/bgr/rgbMasks/{j}", 0)
            if img is not None and np.mean(img) > 0:
                cnt, hir = cv2.findContours(img, cv2.RETR_CCOMP, cv2.CHAIN_APPROX_NONE)
                sand.createFeatures(cnt, hir)
exit(str(sand.thinness))

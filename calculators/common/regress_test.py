import matplotlib.pyplot as plt

from regress import *


if __name__ == '__main__':
    # Example usage:
    x = np.array([1, 2, 3, 4, 5, 6, 7, 8, 9, 10])
    y = np.array([2, 4, 5, 4, 5, 8, 9, 10, 12, 30])  # Add an outlier

    # Perform ordinary least squares linear regression
    slope_ols, intercept_ols, r_value_ols, p_value_ols, stderr_ols = ols_linregress(
        x, y)

    print("Ordinary Least Squares Regression Results:")
    print("Slope:", slope_ols)
    print("Intercept:", intercept_ols)
    print("R-value:", r_value_ols)
    print("P-value:", p_value_ols)
    print("Standard Error of the slope:", stderr_ols)

    # Perform robust linear regression
    slope_robust, intercept_robust, r_value_robust, p_value_robust, stderr_robust = robust_linregress(
        x, y)

    print("\nRobust Regression Results:")
    print("Slope:", slope_robust)
    print("Intercept:", intercept_robust)
    print("R-value:", r_value_robust)
    print("P-value:", p_value_robust)
    print("Standard Error of the slope:", stderr_robust)

    # Plot the data and the regression lines
    plt.figure()
    plt.scatter(x, y, label='Data with outlier')
    plt.plot(x, slope_ols * x + intercept_ols,
             color='red', label='Ordinary Least Squares')
    plt.plot(x, slope_robust * x + intercept_robust,
             color='green', label='Robust Regression (HuberT)')
    plt.xlabel('x')
    plt.ylabel('y')
    plt.title('Comparison of Robust and Ordinary Least Squares Regression')
    plt.legend()
    plt.grid(True)
    plt.show()

    # Example forcing through origin
    slope_origin_ols, intercept_origin_ols, r_value_origin_ols, p_value_origin_ols, stderr_origin_ols = ols_linregress(
        x, y, force_origin=True)
    print("\nOrdinary Least Squares Regression Through Origin:")
    print("Slope:", slope_origin_ols)
    print("Intercept:", intercept_origin_ols)
    print("R-value:", r_value_origin_ols)
    print("P-value:", p_value_origin_ols)
    print("Standard Error of the slope:", stderr_origin_ols)

    slope_origin_robust, intercept_origin_robust, r_value_origin_robust, p_value_origin_robust, stderr_origin_robust = robust_linregress(
        x, y, force_origin=True)
    print("\nRobust Regression Through Origin:")
    print("Slope:", slope_origin_robust)
    print("Intercept:", intercept_origin_robust)
    print("R-value:", r_value_origin_robust)
    print("P-value:", p_value_origin_robust)
    print("Standard Error of the slope:", stderr_origin_robust)

    plt.figure()
    plt.scatter(x, y, label='Data with outlier')
    plt.plot(x, slope_origin_ols * x + intercept_origin_ols,
             color='blue', label='OLS Through Origin')
    plt.plot(x, slope_origin_robust * x + intercept_origin_robust,
             color='purple', label='Robust Through Origin')
    plt.xlabel('x')
    plt.ylabel('y')
    plt.title('Regression Through Origin')
    plt.legend()
    plt.grid(True)
    plt.show()

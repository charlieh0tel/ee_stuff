import numpy as np
import scipy.stats as stats
import statsmodels.api as sm
from statsmodels.robust import robust_linear_model as rlm
from statsmodels.robust.norms import HuberT


def ols_linregress(x, y, force_origin=False):
    x = np.asarray(x)
    y = np.asarray(y)

    if force_origin:
        # Perform regression through the origin by not including a constant
        #  The model is forced to pass through (0,0)
        model = sm.OLS(y, x).fit()
        slope = model.params[0]  # Get slope
        intercept = 0.0         # Intercept is 0
        stderr = model.bse[0]
        p_value = model.pvalues[0] # Get p-value for slope
    else:
        # Add a constant term to x, required by statsmodels
        #  This allows the model to estimate the intercept
        x = sm.add_constant(x)
        # Perform the ordinary least squares regression
        model = sm.OLS(y, x).fit()
        slope = model.params[1]  # Get slope
        intercept = model.params[0]  # Get intercept
        stderr = model.bse[1]
        p_value = model.pvalues[1] # Get p-value for slope

    r_value = np.sqrt(model.rsquared)

    return slope, intercept, r_value, p_value, stderr


def robust_linregress(x, y, a=1.345, force_origin=False):
    x = np.asarray(x)
    y = np.asarray(y)

    if force_origin:
        # Perform regression through the origin by not including a constant
        model = rlm.RLM(y, x, M=HuberT()).fit()
        slope = model.params[0]
        intercept = 0.0
        stderr = model.bse[0]
    else:
        # Add a constant term to x, required by statsmodels
        x = sm.add_constant(x)
        # Perform the robust regression using Huber's T norm
        model = rlm.RLM(y, x, M=HuberT()).fit()
        slope = model.params[1]
        intercept = model.params[0]
        stderr = model.bse[1]

    # Approximate R-value: Use a basic approximation.  RLM doesn't
    # directly provide R-squared.
    y_mean = np.mean(y)
    tss = np.sum((y - y_mean) ** 2)
    ess = np.sum((model.fittedvalues - y_mean) ** 2)
    r_squared = ess / tss if tss > 0 else 0.0  # Handle the case where TSS is zero
    r_value = np.sqrt(r_squared)

    # Approximate p-value: Use a z-test approximation for the p-value
    z_value = slope / stderr if stderr > 0 else 0.0  # avoid division by 0
    p_value = 2 * (1 - stats.norm.cdf(np.abs(z_value)))

    return slope, intercept, r_value, p_value, stderr

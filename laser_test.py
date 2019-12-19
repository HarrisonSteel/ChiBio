# generate gaussian data
from numpy.random import seed
from numpy.random import randn
from numpy import mean
from numpy import std
import numpy as np
from matplotlib import pyplot
from scipy.stats import shapiro
import scipy
import scipy.stats as stats
import pylab
from sklearn.metrics import mean_squared_error, r2_score
import pandas as pd

from os import listdir
from os.path import isfile, join
import math
import itertools
from scipy.optimize import curve_fit


def do_stat_analysis(data, device_data, data_dir,SHOW_FIGS):

    # Shapiro-Wilk Test
    # seed the random number generator
    # normality test
    stat, p = shapiro(data)
    print('Statistics=%.3f, p=%.3f' % (stat, p))
    # interpret
    alpha = 0.05
    if p > alpha:
        res = 'looks G \n(fail to reject H0) a:%g p:%g' % (alpha, p)
    else:
        res = 'does not look G\n (reject H0) a:%g p:%g' % (alpha, p)

    # Determine the number of sample
    # https://stats.stackexchange.com/questions/341358/how-many-samples-do-i-need-to-estimate-a-gaussian-distribution

    # SUPPORTED CONFIDENCE LEVELS: 50%, 68%, 90%, 95%, and 99%
    confidence_level_constant = {50: .67, 68: .99, 90: 1.64, 95: 1.96, 99: 2.57}

    data_var = np.var(data)
    margin_of_error = 0.01*mean(data)
    confidence_level = 95
    sample_num = (confidence_level_constant[confidence_level]/margin_of_error)**2*data_var
    sample_num = round(sample_num)
    print("SAMPLE SIZE: %d" % sample_num)

    # summarize
    data_stat = 'mean=%.3f stdv=%.3f' % (mean(data), std(data))

    # histogram plot
    fig, axs = pyplot.subplots(1, 2, constrained_layout=True)
    fig.suptitle('N=%d SN: %d %s OD:%s ID: %s' % (len(data), sample_num, device_data['dev_name'], device_data['OD'],
                                                  device_data['device_id']))
    axs[0].hist(data)
    axs[0].set_title(data_stat)
    # QQ Plot
    stats.probplot(data, dist="norm", plot=pylab)
    axs[1].set_title('S-W Test: %s'%res)
    if SHOW_FIGS:
        pyplot.show()
    od_str = str(device_data['OD']).replace('.', '_')
    file_name = '%s_%s_%s.png' % (device_data['dev_name'], od_str, device_data['device_id'])
    fig.savefig('%s/%s' % (data_dir, file_name), dpi=fig.dpi)
    pyplot.close(fig)
    return file_name

    # data2 = 5 * randn(100) + 50
    #
    # F = np.var(data) / np.var(data2)
    # df1 = len(data) - 1
    # df2 = len(data2) - 1
    #
    # alpha = 0.05  # Or whatever you want your alpha to be.
    # p_value = scipy.stats.f.cdf(F, df1, df2)
    # print(p_value)
    # if p_value > alpha:
    #     print('Reject the null hypothesis that Var(X) == Var(Y)')

# based on https://machinelearningmastery.com/a-gentle-introduction-to-normality-tests-in-python/


def cost_fcn_quad(x, a, b):
    if a < 0:
        return math.inf
    return a*x**2+b*x


def cost_fcn_lin(x, a):
    return a*x

SHOW_FIGS = False

# seed the random number generator
seed(1)

report_tex_str = ''
# read device names if available
df_dev_names = pd.read_csv('config/device_names.csv')
# placeholders for device specific columns
df_dev_names["fit_quad_coeff"] = np.nan
df_dev_names["fit_lin_coeff"] = np.nan
df_dev_names["fit_r_square"] = np.nan

# read data from a file
data_dir = 'laser_data_new_batch'
onlyfiles = [f for f in listdir(data_dir) if isfile(join(data_dir, f))]

df = None
first = True
for data_file in onlyfiles:
    ext = data_file.split('.')

    if ext[1] == 'csv':
        device_tmp = ext[0].split('_')
        device_data = {'dev_pos': device_tmp[2], 'OD': '%s.%s' % (device_tmp[3], device_tmp[4]), 'ID': device_tmp[5]}
        with open(data_dir + '/' + data_file, 'r') as f:
            data = f.readlines()
            data = [float(i.strip('\n')) for i in data]
            data = np.array(data)
            data_num = len(data)
            data_dict = {'id': [device_tmp[5]]*data_num, 'od': ['%s.%s' % (device_tmp[3], device_tmp[4])]*data_num,
                         'device_id': [device_tmp[2]]*data_num, 'raw': data, 'od_int': [device_tmp[4]]*data_num}
            if first:
                df = pd.DataFrame(data_dict)
                first = False
            else:
                df = pd.concat([df, pd.DataFrame(data_dict)],ignore_index=True)

df['od'] = df['od'].apply(pd.to_numeric, errors='coerce')


df.to_csv('OD_calib.csv')

for dev_id in pd.unique(df['id']):
    M = df[df.id == dev_id]['device_id'].iloc[0]
    device_name = df_dev_names[(df_dev_names.device_id == dev_id)]['device_name'].iloc[0]

    # build report latex
    report_tex_str += '\section{%s}\label{sec:%s}\n \\begin{center}\n' % (device_name, device_name.lower())

    od_i = dict()
    od_i_median = dict()
    od_levels = [0.114, 0.231, 0.367, 0.487, 0.613, 0.733, 0.846]
    od_levels_int = [114, 231, 367, 487, 613, 733, 846]
    sample_num = 20

    # compute histogram and do a normality test for water or medium
    raw_readings = df[(df.id == dev_id) & (df.od_int == str(0))]['raw']
    device_data = {'dev_name': device_name, 'OD': 0.0, 'device_id': dev_id}
    fig_file_name = do_stat_analysis(data=raw_readings, device_data=device_data, data_dir=data_dir,SHOW_FIGS=SHOW_FIGS)
    # build report latex
    report_tex_str += '\includegraphics[scale=0.49]{%s}\n' % fig_file_name

    for act_od, act_od_int in zip(od_levels, od_levels_int):
        # calculate OD_i samples
        blank_sample = df[(df.id == dev_id) & (df.od == 0.0)]['raw'].sample(n=sample_num)
        raw_sample = df[(df.id == dev_id) & (df.od_int == str(act_od_int))]['raw'].sample(n=sample_num)
        sample_combininations = list(itertools.product(blank_sample, raw_sample))
        od_i[act_od] = list(map(lambda x: math.log10(x[0] / x[1]), sample_combininations))
        # calculate OD_i median
        blank_median = df[(df.id == dev_id) & (df.od == 0.0)]['raw'].median()
        raw_median = df[(df.id == dev_id) & (df.od_int == str(act_od_int))]['raw'].median()
        od_i_median[act_od] =  math.log10(blank_median/raw_median)
        # compute histogram and do a normality test
        raw_readings = df[(df.id == dev_id) & (df.od_int == str(act_od_int))]['raw']
        device_data = {'dev_name': device_name, 'OD': act_od, 'device_id': dev_id}
        fig_file_name = do_stat_analysis(data=raw_readings, device_data=device_data, data_dir=data_dir,SHOW_FIGS=SHOW_FIGS)
        # build report latex
        report_tex_str += '\includegraphics[scale=0.49]{%s}\n' % fig_file_name

    fig = pyplot.figure()
    pyplot.title('Dev name: %s ID: %s' % (device_name, dev_id))
    x = list()
    y = list()
    yy = list()
    for act_od in od_levels:
        tmp_x = [act_od]*len(od_i[act_od])
        x += tmp_x
        tmp_y = od_i[act_od]
        y += tmp_y
        pyplot.scatter(tmp_x, tmp_y,  color='green')
    pyplot.scatter(od_levels, od_i_median.values(),  color='red')
    # fitting a quadratic
    z_quad, pcov_quad = curve_fit(f=cost_fcn_quad, xdata=y, ydata=x)
    y_pred_quad = [z_quad[0]*x_act**2+z_quad[1]*x_act for x_act in y]
    coefficient_of_determination_quad = r2_score(x, y_pred_quad)
    # save quad fitting for later use
    df_dev_names.loc[df_dev_names.device_id == dev_id, 'fit_quad_coeff'] = z_quad[0]
    df_dev_names.loc[df_dev_names.device_id == dev_id, 'fit_lin_coeff'] = z_quad[1]
    df_dev_names.loc[df_dev_names.device_id == dev_id, 'fit_r_square'] = coefficient_of_determination_quad
    # fitting linear
    z_lin, pcov_lin = curve_fit(f=cost_fcn_lin, xdata=y, ydata=x)
    y_pred_lin = [z_lin[0]*x_act for x_act in y]
    coefficient_of_determination_lin = r2_score(x, y_pred_lin)

    # Chi.bio paper fit
    y_pred_chibio = [-0.397*x_act**2+1.374*x_act for x_act in y]
    coefficient_of_determination_chibio = r2_score(x, y_pred_chibio)

    od_x_axis = np.linspace(0,1,11)
    pyplot.plot(z_quad[0]*od_x_axis**2+z_quad[1]*od_x_axis,od_x_axis, color='blue')
    pyplot.plot(z_lin[0]*od_x_axis,od_x_axis, color='red')
    pyplot.plot(0.397*od_x_axis**2+1.374*od_x_axis, od_x_axis, color='black')
    pyplot.legend(('Fit: $x=%gy^2+%gy$ | $r^2:%g$' % (z_quad[0], z_quad[1], coefficient_of_determination_quad),
                   'Fit: $x=%gy$ | $r^2: %g$' % (z_lin[0], coefficient_of_determination_lin),
                   'Chi.Bio paper: $x=0.397y^2+1.374y$ | $r^2:%g$' % coefficient_of_determination_chibio))

    pyplot.xlabel('$OD~[cm^{-1}]$ Data source: Spectrophotometer')
    pyplot.ylabel('$OD_i$ Data source: Chi.Bio')
    pyplot.text(0.4, 0.05, '$OD_i$ sample num: %d, R sample num: %d'%(sample_num, sample_num))
    curve_fit_file_name = '%s_%s.png' % (device_name, dev_id)
    fig.savefig('%s/%s' % (data_dir, curve_fit_file_name))
    if SHOW_FIGS:
        pyplot.show()
    pyplot.close(fig)
    # build report latex
    report_tex_str += '\includegraphics[scale=0.49]{%s}\n' % curve_fit_file_name
    report_tex_str +='\end{center}\n'

# save the device config
df_dev_names.to_csv('config/device_config.csv',index=False)

# write out the latex report
with open('%s/report.tex' % data_dir, 'w') as f:
    # open and write the latex header
    with open('%s/report_header.tex' % data_dir) as f_header:
        for header_lines in f_header:
            f.write(header_lines)
    # write the data
    f.write(report_tex_str)
    # write summary data
    f.write(df_dev_names.to_latex(index=False))
    # openn and write the footer
    with open('%s/report_footer.tex' % data_dir) as f_footer:
        for footer_line in f_footer:
            f.write(footer_line)




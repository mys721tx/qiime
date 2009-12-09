#!/usr/bin/env python
# file distance_histograms.py

__author__ = "Jeremy Widmann"
__copyright__ = "Copyright 2009, the PyCogent Project"
__credits__ = ["Jeremy Widmann","Rob Knight"]
__license__ = "GPL"
__version__ = "0.1"
__maintainer__ = "Jeremy Widmann"
__email__ = "jeremy.widmann@colorado.edu"
__status__ = "Prototype"

from matplotlib import use
use('Agg')
from qiime.parse import parse_map, parse_distmat, group_by_field,\
    group_by_fields
from qiime.make_3d_plots import create_dir, data_colors
from cogent.maths.stats.test import t_two_sample
from numpy import array, mean, average, arange
from collections import defaultdict
from string import strip
from matplotlib.pylab import savefig, clf, gca, gcf,close
from cogent.draw.util import hist
from matplotlib.patches import Ellipse, Polygon
from random import choice
from numpy.random import permutation
from sys import argv
from os import mkdir
from optparse import make_option, OptionParser

def between_sample_distances(dmat):
    """Returns all upper triangle distances from dmat.
    """
    distances = []
    dmat_len = len(dmat)
    for i in range(dmat_len):
        for j in range(i+1,dmat_len):
            distances.append(dmat[i][j])
    return {'All_Between_Sample_Distances':distances}

def within_category_distances_grouped(single_field):
    """Returns all within category distances grouped for every field.
    
        - single_field is from calling group_distances and taking single_field
            result.
    """
    distances = defaultdict(list)
    for field, groups in single_field.items():
        for data in groups:
            if data[0] == data[1]:
                all = array(data[2])
                distances[field+\
                    '_All_Within_Category_Distances'].extend(all.flat)
    return distances

def between_category_distances_grouped(single_field):
    """Returns all between category distances grouped for every field.
    
        - single_field is from calling group_distances and taking single_field
            result.
    """
    distances = defaultdict(list)
    for field, groups in single_field.items():
        for data in groups:
            if data[0] != data[1]:
                all = array(data[2])
                distances[field+\
                    '_All_Between_Category_Distances'].extend(all.flat)
    return distances

def within_category_distances(single_field):
    """Returns all within category distances, broken down by category.
    
        - single_field is from calling group_distances and taking single_field
            result.
    """
    distances = defaultdict(list)
    for field, groups in single_field.items():
        for data in groups:
            if data[0] == data[1]:
                all = array(data[2])
                distances[field+'_Within_'+data[0]+\
                    '_Distances'].extend(all.flat)
    return distances

def within_and_between_fields(paired_field):
    """Returns all within field and all between field comparisons.
    
        - paired_field is from calling group_distances and taking paired_field
            result.
    """
    distances = defaultdict(list)
    for field, groups in paired_field.items():
        first, second = field.split('_to_')
        if first == second:
            for data in groups:
                if data[0] != data[1]:
                    continue
                all = array(data[2])
                distances['Within_All_Fields'].extend(all.flat)
        else:
            for data in groups:
                if data[0] == data[1]:
                    continue
                all = array(data[2])
                distances['Between_All_Fields'].extend(all.flat)
    return distances

def all_category_distances(single_field):
    """Returns all within category distances, broken down by category.
    
        - single_field is from calling group_distances and taking single_field
            result.
    """
    distances = defaultdict(list)
    for field, groups in single_field.items():
        for data in groups:
            all = array(data[2])
            distances[field+'_'+data[0]+'_to_'+data[1]].extend(all.flat)
    return distances

def draw_all_histograms(single_field, paired_field, dmat, histogram_dir):
    """Draws all combinations of histograms.
    """
    #make dict of label to histogram filename
    label_to_histogram_filename = {}
    
    #list of different distances
    distances_dict = {}
    
    #Get all between sample distances
    all_between = between_sample_distances(dmat)
    distances_dict['All_Between_Sample_Distances']=all_between
    
    label_to_histogram_filename.update(\
        _make_histogram_filenames(all_between,histogram_dir))
    
    #Get all within category distances grouped together
    all_within_category_grouped = \
        within_category_distances_grouped(single_field)
    distances_dict['All_Within_Category_Grouped']=all_within_category_grouped
    
    label_to_histogram_filename.update(\
        _make_histogram_filenames(all_within_category_grouped,histogram_dir))

    #Get all between category distances grouped together
    all_between_category_grouped = \
        between_category_distances_grouped(single_field)
    distances_dict['All_Between_Category_Grouped']=all_between_category_grouped
    
    label_to_histogram_filename.update(\
        _make_histogram_filenames(all_between_category_grouped,histogram_dir))

    
    #Get all within category distances by category
    all_within_category_individual = \
        within_category_distances(single_field)
    distances_dict['All_Within_Categories']=all_within_category_individual
    
    label_to_histogram_filename.update(\
        _make_histogram_filenames(all_within_category_individual,histogram_dir))
    
    #Get all within and between field distances
    all_within_and_between_fields = within_and_between_fields(paired_field)
    distances_dict['All_Within_And_Between_Fields']=\
        all_within_and_between_fields

    label_to_histogram_filename.update(\
        _make_histogram_filenames(all_within_and_between_fields,histogram_dir))

    #Get all category distances
    all_categories = all_category_distances(single_field)
    distances_dict['All_Category_Pairs']=all_categories

    label_to_histogram_filename.update(\
        _make_histogram_filenames(all_categories,histogram_dir))

    
    num_colors = len(data_colors)
    BINS=arange(0,1.01,0.05)
    xscale, yscale = get_histogram_scale(distances_dict,nbins=BINS)
    #draw histograms
    color_names = data_colors.keys()
    for d_dict in distances_dict.values():
        for i, (field, data) in enumerate(d_dict.items()):
            if len(data) < 1:
                continue
            color_index = i % num_colors
            color = color_names[color_index]
            outfile_name = label_to_histogram_filename[field]
            histogram = draw_histogram(distances=data, color=color, nbins=BINS, \
                outfile_name=outfile_name,xscale=xscale,yscale=yscale)
    
    return distances_dict, label_to_histogram_filename

def get_histogram_scale(distances_dict, nbins):
    """Draws histogram to outfile_name.
    """
    scale_dict = defaultdict(list)
    #draw histograms
    for d_dict in distances_dict.values():
        for i, (field, data) in enumerate(d_dict.items()):
            if len(data) < 1:
                continue
            histogram = hist(data,bins=nbins)
            
            fig  = gcf()
            axis = fig.gca()

            #get height scale: y/x
            ymin,ymax = axis.get_ylim()
        
            xmin,xmax = axis.get_xlim()
            scale_dict['ymin'].append(ymin)
            scale_dict['ymax'].append(ymax)
            scale_dict['xmin'].append(xmin)
            scale_dict['xmax'].append(xmax)

            clf()
    
    yscale = (min(scale_dict['ymin']),max(scale_dict['ymax']))
    xscale = (min(scale_dict['xmin']),max(scale_dict['xmax']))
    
    return xscale,yscale

def draw_histogram(distances, color, nbins, outfile_name,\
    xscale=None, yscale=None, title='', **kwargs):
    """Draws histogram to outfile_name.
    """
    average = mean(distances)
    maximum = max(distances)
    
    histogram = hist(distances,bins=nbins,facecolor=color, \
        normed=True,**kwargs)
    
    fig  = gcf()
    axis = fig.gca()
    
    #set labels
    axis.set_xlabel('Distance')
    axis.set_ylabel('Normalized Counts of Pairs in Group')
    axis.set_title(title)
    #get figure scale: width/height
    fig_scale = fig.get_figwidth()/float(fig.get_figheight())
    
    if xscale is not None:
        axis.set_xlim(xscale)
    if yscale is not None:
        axis.set_ylim(yscale)
    
    #get height scale: y/x
    ylim = axis.get_ylim()
    ylen = ylim[1]-ylim[0]
    xlim = axis.get_xlim()
    xlen = xlim[1]-xlim[0]
    height_scale = ylen/float(xlen)
    
    #set width
    width = xlen/20.
    height = width*height_scale*fig_scale
    
    #draw circle at average distance
    ellipse = Ellipse([average,0.0],width=width, \
        height=height, \
        edgecolor=color, fill=False)
    axis.add_artist(ellipse)        
    #draw line at center of circle
    y1 = -height/2.
    y2 = height/2.

    line = Polygon([[average, y1] ,[average, y2]], edgecolor=color)
    axis.add_artist(line)


    savefig(outfile_name,format='png',dpi=75, transparent=True)

    close()
    return histogram

NAV_HTML_TR = '''<span class="smnorm"><input type="checkbox" id="%s" %s onclick="visibilityAndOpacity(this, %s)" />
<a onmouseover="mouseoverVisible(%s)"; onmouseout="mouseoverHidden(%s)">%s</a></span><br />'''

NAV_HTML_TR_BREAK = '''<span class="normal">%s</span><br />'''

NAV_HTML_FRAME_START = '''<td>
    <div style="overflow:scroll; width: 300px; height: 400px;">
    
    <p>
'''
NAV_HTML_FRAME_END = '''
    </p>
    </div>
    </td>
'''

FULL_HTML_TITLE_FRAME = """
<html><head> <title>
%s
</title>
<script type="text/javascript" src="./js/histograms.js"></script>
 <style type="text/css">
.smnorm {color: blue; font-family:Arial,Verdana; font-size:10; font-weight: bold;}
.normal {color: black; font-family:Arial,Verdana; font-size:11; font-weight: bold;}
"""
FULL_HTML_JS_FRAME = """
</style>
</head>
<body> 
<div id="overDiv" style="position:absolute; visibility:hidden; z-index:1000;"></div>
<table width="200" border="0" cellspacing="2" cellpadding="2"> <table width="200" border="0" cellspacing="2" cellpadding="2"> <tr><td colspan="2" class="header_qiime" align="center">
    <table width=800 cellpadding=0 cellspacing=0 border=0>
    <tr valign=middle><td class=ntitle width=200 valign="middle"><img src="./web_resources/qiime_header.png" border="0" /></td>
        <td width=300 align=center >
            &nbsp; 
        </td>
    </tr> 
    </table>
</td></tr>
<tr><td colspan="2" align="left" valign="top">&nbsp;</td></tr> 
 </table>  <tr><td colspan="2" align="left" valign="top" class="normal"> <table border="0" cellspacing="1" cellpadding="0" width="800">

</table>  </td> </tr> </table>
"""

FULL_HTML_MAIN_IMAGE = '''<div>
    <table>
        <tr>
            %s
        </tr>
    </table>
</div>

'''

SINGLE_IMAGE_BLOCK = '''
<td style="position:absolute; top:100; left:0;">
<img style="z-index:1; opacity:1.0;filter:alpha(opacity=100); visibility:%s;" id="%s" name="%s" src="%s" border="0"></td>'''

FULL_HTML_NAV_FRAME = """
<table style="position:absolute; top:100; left:600">
    <tr>
    %s
    </tr>
</table>
"""

def make_nav_html(distances_dict, label_to_histogram_filename, \
    default='All_Between_Sample_Distances'):
    """Returns HTML string with mouseover table linked to filenames.
    """
    html_list = []
    for main_block, distances in distances_dict.items():
        html_list.append(NAV_HTML_TR_BREAK%(main_block))
        for sub_label in sorted(distances.keys()):
            hist_filename = label_to_histogram_filename[sub_label].strip('./')
            hist_filename = "'"+hist_filename+"'"
            checked = ''
            if main_block == default:
                checked = 'checked'
            sub_label_quoted = "'"+sub_label+"'"
            html_list.append(NAV_HTML_TR%\
                ('check_'+sub_label, checked, \
                    sub_label_quoted, sub_label_quoted,\
                    sub_label_quoted, sub_label))
    nav_html = '\n'.join(html_list)
    return NAV_HTML_FRAME_START + nav_html + NAV_HTML_FRAME_END

def make_main_html(distances_dict, label_to_histogram_filename, root_outdir, \
    outfile_name, title='QIIME - Distance Histograms', \
    default='All_Between_Sample_Distances'):
    """Returns full HTML string to show distance histograms.
    """
    main_html_list = []
    #Add title HTML
    main_html_list.append(FULL_HTML_TITLE_FRAME%(title))
    
    #Add javascript in html
    main_html_list.append(FULL_HTML_JS_FRAME)
    
    #Add default image HTML
    all_images = []
    all_images.append(SINGLE_IMAGE_BLOCK%('visible',default,'visible',\
        label_to_histogram_filename[default]))
        
    for i,(name,src) in enumerate(label_to_histogram_filename.items()):
        all_images.append(SINGLE_IMAGE_BLOCK%('hidden',\
            name,'hidden',src))
        
    main_html_list.append(FULL_HTML_MAIN_IMAGE%('\n'.join(all_images)))
    
    #Add nav html
    nav_html = make_nav_html(distances_dict, label_to_histogram_filename)
    main_html_list.append(FULL_HTML_NAV_FRAME%(nav_html))
    
    main_html_out = open(root_outdir+'/'+outfile_name,'w')
    main_html_out.write(''.join(main_html_list))
    main_html_out.close

def get_valid_indices(input_items, wanted_items):
    """returns indices of wanted_items in input_items if present."""
    try:
        return map(input_items.index, wanted_items)
    except ValueError:  #missing ids?
        return [input_items.index(i) for i in wanted_items\
            if i in input_items]

def distances_by_groups(distance_header, distance_matrix, groups):
    """Splits distances by group membership, returns vals for each pair.
    
    Omits the zeros along the diagonal.
    """
    result = []
    group_items = groups.items()
    for i, (row_group, row_ids) in enumerate(group_items):
        row_indices = get_valid_indices(distance_header, row_ids)
        #handle the case where indices are separate: just return blocks
        for j in range(i+1, len(groups)):
            col_group, col_ids = group_items[j]
            col_indices = get_valid_indices(distance_header, col_ids)
            vals = distance_matrix[row_indices][:,col_indices]
            result.append([row_group, col_group, vals])
        #handle the case where indices are the same so need to omit diag
        block = distance_matrix[row_indices][:,row_indices]
        size = len(row_indices)
        indices = []
        for i in range(size):
            for j in range(size):
                if i != j:
                    indices.append(i*size+j)
        result.append([row_group, row_group, block.flat[indices]])
    return result

def write_distance_files(group_distance_dict,dir_prefix = '', \
    subdir_prefix='distances'):
    """writes distance files for each col of mapping file."""
    path_prefix = _make_path([dir_prefix,subdir_prefix])
    try:
        mkdir(path_prefix)
    except OSError:     #raised if dir exists
        pass

    for field, data in group_distance_dict.items(): #skip sample id field
        fname = path_prefix  + 'dist_' + field + '.xls'
        outfile = open(fname, 'w')
        for d in data:
            outfile.write('\t'.join([str(d[0])+'_to_'+str(d[1])] + \
                map(str, d[2].flat)))
            outfile.write('\n')
        outfile.close()


def group_distances(mapping_file,dmatrix_file,fields,dir_prefix='',\
    subdir_prefix='group_distances'):
    """Calculate all lists of distance groups."""
    distance_groups = {}
    mapping = parse_map(open(mapping_file,'U'))
    distance_header, distance_matrix = \
        parse_distmat(open(dmatrix_file,'U'))
    if fields is None:
        fields = [mapping[0][0]]
    single_field = defaultdict(dict)
    for i in range(len(fields)):
        field = fields[i]
        groups = group_by_field(mapping, field)
        data = distances_by_groups(distance_header, distance_matrix, groups)
        single_field[field]=data

    write_distance_files(group_distance_dict=single_field,\
        dir_prefix=dir_prefix,subdir_prefix=subdir_prefix+'_single')
        
    paired_field = defaultdict(dict)
    for i in range(len(fields)):
        for j in range(i,len(fields)):
            fieldi = fields[i]
            fieldj = fields[j]
            groups = group_by_fields(mapping, [fieldi,fieldj])
            data = distances_by_groups(distance_header, distance_matrix, groups)
            paired_field[fieldi+'_to_'+fieldj]=data

    write_distance_files(group_distance_dict=paired_field,\
        dir_prefix=dir_prefix,subdir_prefix=subdir_prefix+'_pairs')
    
    return single_field, paired_field, distance_matrix

def monte_carlo_group_distances(mapping_file, dmatrix_file, prefs, \
    dir_prefix = '', subdir_prefix='monte_carlo_group_distances'):
    """Calculate Monte Carlo stats for specified group distances.
    
    Specifically:
    - find the groups for each specified col (or combination of cols)
    - do t test between each pair of groups
    - randomize matrix n times and find empirical value of t for each pair
    - compare the actual value of t to the randomized values
    """
    mapping = parse_map(open(mapping_file,'U'))
    distance_header, distance_matrix = \
        parse_distmat(open(dmatrix_file,'U'))
    orig_distance_matrix = distance_matrix.copy()

    path_prefix = _make_path([dir_prefix,subdir_prefix])
    try:
        mkdir(path_prefix)
    except OSError:     #raised if dir exists
        pass
    


    for field, num_iters in prefs['MONTE_CARLO_GROUP_DISTANCES'].items():
        if '&&' in field:
            groups = group_by_fields(mapping, field.split('&&'))
        else:
            groups = group_by_field(mapping, field)
        outfile = open(path_prefix+'group_distances_'+field+'.xls', 'w')
        real_dists = distances_by_groups(distance_header, distance_matrix,\
            groups)
        rand_distances = [distances_by_groups(distance_header, \
            permute_for_monte_carlo(distance_matrix), groups) \
            for i in range(num_iters)]
        #iterate over the groups
        for i, (first_g1, second_g1, distances_g1) in \
            enumerate(real_dists[:-1]):
            real_dist_1 = average(distances_g1)
            rand_dists_1 = [rand_distances[n][i][-1] for n in range(num_iters)]
            #then for each other pair (not including same group)
            for j in range(i+1,len(real_dists)):
                first_g2, second_g2, distances_g2 = real_dists[j]
                real_dist_2 = average(distances_g2)
                rand_dists_2 = [rand_distances[n][j][-1] \
                    for n in range(num_iters)]
                ttests = [t_two_sample(rand_dists_1[n],rand_dists_2[n])[0] \
                    for n in range(num_iters)]
                real_ttest = t_two_sample(distances_g1, distances_g2)
                curr_line = [first_g1, 'to', second_g1, 'avg', real_dist_1, \
                    'compared with', first_g2, 'to', second_g2, 'avg', \
                    real_dist_2]
                curr_line.extend([': t=', real_ttest[0], 'p=', real_ttest[1],
                    'p_greater:', \
                    (array(ttests)>real_ttest[0]).sum()/float(num_iters), \
                    'p_less:', 
                    (array(ttests)<real_ttest[0]).sum()/float(num_iters), \
                    'num_iters:', num_iters])
                outfile.write('\t'.join(map(str, curr_line)))
                outfile.write('\n')

def permute_for_monte_carlo(dist_matrix):
    """Returns permuted copy of distance matrix for Monte Carlo tests."""
    size = len(dist_matrix)
    p = permutation(size)
    return dist_matrix[p][:,p]

def _make_histogram_filenames(distances,histogram_dir):
    """From distances dict, returns dict of keys to histogram filenames.
    
        - distances: dict of label to distances.
        
        returns dict of label to filename: {label: label_randomchars.png}
    """
    filename_dict = {}
    for label in distances.keys():
        filename_dict[label]=_make_random_filename(prefix=\
            histogram_dir+label+'_', \
            suffix='.png')
    
    return filename_dict

def _make_path(paths):
    """join together the paths (e.g. dir and subdir prefix), empty str default"""
    curr = ''
    for p in paths:
        if p:
            curr += p
            if curr and (not curr.endswith('/')):
                curr += '/'
    return curr

def _make_random_filename(prefix='',suffix='',num_chars=20):
    """Returns filename with random characters between prefix and suffix.
    """
    all = 'ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789'
    rand_region = ''.join([choice(all) for i in range(num_chars)])
    return prefix+rand_region+suffix

def _get_script_dir(script_path):
    """Returns directory current script is running in.
    """
    if '/' in script_path:
        script_dir = script_path.rsplit('/',1)[0]+'/'
    else:
        script_dir = './'
    return script_dir
    

OPTIONS = [
        make_option('-d','--distance_matrix_file',dest='distance_matrix_file',\
            type='string',help='''Path to distance matrix file [REQUIRED]'''),\
        make_option('-m','--mapping_file',dest='mapping_file',type='string',\
            help='''Path to environment mapping file [REQUIRED]'''),\
        make_option('-p','--prefs_file',dest='prefs_file',type='string',\
            help='''File containing prefs for analysis.  NOTE: This is a file with a dict containing preferences for the analysis.  This dict must have a "Fields" key mapping to a list of desired fields.[REQUIRED]'''),\
        make_option('-o', '--dir_path', dest='dir_path',\
            help='directory prefix for all analyses [default: %default]',\
            default='.'),\
        make_option('--fields', dest='fields',\
            help='Comma delimited list of fields to compare.  This overwrites fields in prefs file.  Usage: --fields Field1,Field2,Field3'),\
        make_option('--monte_carlo',dest='monte_carlo',default=False,\
            action='store_true',help='''Perform Monte Carlo on distances.  [Default: %default]'''),\
        make_option('--html_output',dest='html_output',default=False,\
            action='store_true',help='''Write output in HTML format. [Default: %default]'''),\
        ]


def parse_cmdline_params(arg_list=argv,options=OPTIONS):
    """Parses commandline arguments.
    """
    usage = 'usage: $ python %prog [options]'
    version = 'Version: %prog 0.1'
    
    options_parser = OptionParser(usage=usage,version=version,\
        option_list=options)
    opts,args = options_parser.parse_args(args=arg_list)
    
    return opts, args

def main(args,args_parsed=None):
    qiime_dir = _get_script_dir(argv[0])

    if args_parsed is not None:
        opts = args_parsed
    else:
        opts,arg_list = parse_cmdline_params(args)        
    

    prefs = eval(open(opts.prefs_file, 'U').read())
    fields = opts.fields
    if fields is not None:
        fields = map(strip,fields.split(','))
    else:
        fields = prefs['FIELDS']
    
    within_distances, between_distances, dmat = \
        group_distances(mapping_file=opts.mapping_file,\
        dmatrix_file=opts.distance_matrix_file,\
        fields=fields,\
        dir_prefix=create_dir(opts.dir_path,'distances'))
    
    if opts.html_output:
        #histograms output path
        histograms_path = \
            _make_path([opts.dir_path,'histograms'])
        try:
            mkdir(histograms_path)
        except OSError:     #raised if dir exists
            pass
        
        #draw all histograms
        distances_dict, label_to_histogram_filename = \
            draw_all_histograms(single_field=within_distances, \
                paired_field=between_distances, \
                dmat=dmat,\
                histogram_dir=histograms_path)
        
        outfile_name = 'QIIME_Distance_Histograms.html'
        make_main_html(distances_dict=distances_dict,\
            label_to_histogram_filename=label_to_histogram_filename,\
            root_outdir=opts.dir_path, \
            outfile_name = outfile_name, \
            title='Distance Histograms')
        
        #Handle saving web resources locally.
        #javascript file
        javascript_path = \
            _make_path([opts.dir_path,'js'])
        try:
            mkdir(javascript_path)
        except OSError:     #raised if dir exists
            pass
        js_out = open(javascript_path+'/histograms.js','w')
        js_out.write(open(qiime_dir+'js/histograms.js').read())
        js_out.close()
        
        #Qiime logo
        logo_path = \
            _make_path([opts.dir_path,'web_resources'])
        try:
            mkdir(logo_path)
        except OSError:     #raised if dir exists
            pass
        logo_out = open(logo_path+'/qiime_header.png','w')
        logo_out.write(open(qiime_dir+'qiime_header.png').read())
        logo_out.close()
    
    if opts.monte_carlo:
        monte_carlo_group_distances(mapping_file=opts.mapping_file,\
            dmatrix_file=opts.distance_matrix_file,\
            prefs=prefs, \
            dir_prefix = opts.dir_path)
            
if __name__ == "__main__":
    main(argv)
            

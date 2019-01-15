# module for loading parameters.
import os

#### Base parameters

# These are parameters which users are not likely to need to change.
# We store them in a string of the same format as a parameters file.

baseParamStr = """

#### Blast ####

# blast command line (except for value for evalue as well as db,query
# and outfiles)
blastCLine = 'blastp -matrix BLOSUM62 -gapopen 11 -gapextend 1 -seg yes -outfmt 6 -evalue '

#### Family formation ####

# Family formation involves several thresholds. We determine these by
# looking at histograms of scores.
scoreHistNumBins = 80

## absMinRawThresholdForHomology
# A gene with a raw score below absMinRawThresholdForHomology will not
# be added to a family. If we cannot find a homologous peak in the
# histogram, we will just go with the following default.
defaultAbsMinRawThresholdForHomology = 0.75

# parameters for finding the homologous (right) peak in raw score
# histograms. These put restrictions on the peaks we can
# find. widthRelHeight specifies where we measure the width of a peak,
# as a proportion of the way down from the top.
homologRightPeakLimit = 1.0
widthRelHeight = 0.9

# case 1 (normal case)
homologPeakWidthCase1 = 0.05
homologRequiredProminenceCase1 = 0.4
homologLeftPeakLimitCase1 = 0.65

# case 2 (extreme prominence. But allow to be very narrow)
homologPeakWidthCase2 = 0
homologRequiredProminenceCase2 = 6
homologLeftPeakLimitCase2 = 0.90

# case 3 (wide width with low prominence)
homologPeakWidthCase3 = 0.25
homologRequiredProminenceCase3 = 0.10
homologLeftPeakLimitCase3 = 0.65

# parameters for finding the non-homologous (left) peak in raw score
# histograms.
nonHomologPeakWidth = 0.15
nonHomologPeakProminence = 2
nonHomologLeftPeakLimit = 0
nonHomologRightPeakLimit = 0.6

## synteny threshold parameters

# minSynThreshold is a synteny threshold below which we will not add a
# gene to a family. synAdjustThreshold is a synteny theshold above
# which we make a gene more likely to be added to a family (by bumping
# up it's raw score).

defaultMinSynThreshold = 0.6
defaultSynAdjustThreshold = 0.8

# These increments indicate how much to modify the left extreme of the
# synteny peak to get minSynThreshold or synAdjustThreshold
minSynThresholdIncrement = 0.15
synAdjustThresholdIncrement = 0.02

# finding the homologous (right) synteny peak
synLeftPeakLimit = 0.6
synRightPeakLimit = 1.0

# case 1 (High prominence, narrow peak. Close relatedness
synPeakWidthCase1 = 0.01
synRequiredProminenceCase1 = 2.0

# case 2 (wide width, low prominence. Distant relatedness.)
synPeakWidthCase2 = 0.10
synRequiredProminenceCase2 = 0.1


# We use syntenty scores to adjust similarity scores in family
# finding. In particular, if synteny is very good, we give the raw
# similarity score a little bump to increase the chances of the gene
# under consideration being added to the family. This parameter
# specifies the amount we multiply a rawScore by during this
# adjustment.
synAdjustExtent = 1.05

# When forming gene families within a single strain, we need a raw
# score threshold to determine which genes are similar enough to get
# in the same family. To get this threshold, we identify the nearest
# neighbors of the strain in question, and get the average score in
# core genes across these. We then multiply by this adjustment
# parameter to get the value we use as a threshold.
singleStrainFamilyThresholdAdjust = 0.5

#### Visualization and analysis ####

# The possible rgb values for bed files is based on the list below. 
potentialRgbL = ['245,130,48', '188,143,14','0,102,0','230,26,135','0,0,128', '145,30,180','0,255,255','128,0,0','0,255,0', '255,0,255','240,230,140','32,178,170','240,128,128','255,0,0','100,149,237','60,179,113','0,255,130','128,128,128','94,94,94','102,51,0']

"""


#### Functions
def createParametersD(baseParamStr,paramFN):
    '''Create and return a parameters dictionary. First parses the string
passed in as baseParamStr. This consists of parameters users are less
likely to modify. Then adds user specific parameters contained in the
file paramFN. Note that because the user parameters are put in the
parameters dictionary second, it is possible for a user to override
one of the base parameters simply by including that parameter in their
parameter file.

    '''
    paramD={}
    baseParamL = baseParamStr.split('\n')
    paramD = addParametersToD(baseParamL,paramD)

    f=open(paramFN,'r')
    userParamL = f.read().split('\n')
    paramD = addParametersToD(userParamL,paramD)
    f.close()
    
    return paramD
    
def addParametersToD(paramL,paramD):
    '''Given a list of lines (e.g. from a parameters file) add parameters
to paramD. Each line is a string. Some will be comments or blank
lines, and others will be python assignment statements. We use the
assignment statements to create entries in paramD.
    '''

    for s in paramL:
        if s == '' or s.lstrip() == '' or s.lstrip()[0]=='#':
            continue
        # it's not a blank line, a line with only whitespace or a
        # comment.  so it must be an assignment statement.
        key,value = s.rstrip().split('=')
        key = key.strip()
        value = value.strip()
        paramD[key] = eval(value)
    
    return paramD    
    
def loadFileNameMapD(fileNameMapFN,genbankFileList=None):
    '''Create a dictionary with mappings between genbank file names and
the human readable names we use in the tree. If fileNameMapFN contains
a string, we load that file and construct the mappings based on this.
Expects file with one species per line: genbank name + white space +
human name. If fileNameMapFN is None, we create the mappings between
the full file names (with path and extension) and the stem of the file
name, which in this case should correspond to what is in the input
tree.
    '''
    fileNameMapD = {}
    if fileNameMapFN == None:
        for fullPathFN in genbankFileList:
            fn = os.path.split(fullPathFN)[-1]
            stem = os.path.splitext(fn)[0]
            fileNameMapD[fn] = stem
    else:
        f = open(fileNameMapFN,'r')
        while True:
            s = f.readline()
            if s == '':
                break
            elif s[0].isspace():
                continue
            genbankStem,human = s.rstrip().split()
            fileNameMapD[genbankStem] = human
    return fileNameMapD

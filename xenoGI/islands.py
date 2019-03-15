import sys
from multiprocessing import Pool
from . import trees
from . import genomes
from . import analysis
from .Island import *
from .Family import *
import math 


## temp debugging

def speedTestLocIsl(geneOrderT,geneNames,subtreeL,tree,paramD,familiesO,strainStr2NumD,strainNum2StrD):
    '''Test function to merge locus islands at a single node.'''

    numThreads = paramD['numThreads']
    rootFocalClade = paramD['rootFocalClade']
    islandOutFN = paramD['islandOutFN']
    geneProximityRange = paramD['geneProximityRange']
    proximityThresholdMerge1 = paramD['proximityThresholdMerge1']
    rscThresholdMerge1 = paramD['rscThresholdMerge1']
    
    ## Temp parameters (later add to parameters.py)
    maxClusterSize = 50
    geneProximityRange = 2 # can adjust here for now. Should be >= 1.

    testNode = strainStr2NumD['i0']
    
    ##

    geneProximityD = genomes.createGeneProximityD(geneOrderT,geneProximityRange )
    locIslByNodeL=createLocIslByNodeL(familiesO,tree)
    numIslandsAtEachNodeAtStartL = [len(L) for L in locIslByNodeL]

    subtree = subtreeL[testNode]

    islandsAtMrcaNodeL = locIslByNodeL[testNode]
    
    print("num islands at node to start",len(islandsAtMrcaNodeL))

    writeFamilies(islandsAtMrcaNodeL,'famsi0_initial.txt')


    mrcaClustersL,mrcaSingletonClustersL = createMrcaNodeClusters(islandsAtMrcaNodeL,familiesO,subtree,geneProximityD,proximityThresholdMerge1,maxClusterSize)
    
    writeFamilies(extractFromClusters(mrcaClustersL+mrcaSingletonClustersL),'famsi0_cluster.txt')
    
    


    argumentL = []
    for clusterL in mrcaClustersL:
        argumentL.append((clusterL,geneProximityD,proximityThresholdMerge1,rscThresholdMerge1,subtreeL[clusterL[0].mrca],familiesO))
    p=Pool(numThreads)
    mergedL = p.map(mergeLocIslandsAtNode, argumentL) # run it

    print("num islands after cluster merge",len(extractFromClusters(mergedL+mrcaSingletonClustersL)))

    writeFamilies(extractFromClusters(mergedL+mrcaSingletonClustersL),'famsi0_aftercluster.txt')


    # merge at nodes
    mergedL = mergeLocIslandsAtNode((extractFromClusters(mergedL),geneProximityD,proximityThresholdMerge1,rscThresholdMerge1,subtree,familiesO))

    outputL = mergedL + extractFromClusters(mrcaSingletonClustersL)
    
    print("num islands at end",len(outputL))
    
    writeFamilies(outputL,'famsi0_final.txt')
    
    return outputL

def extractFromClusters(clusterL):

    liL=[]
    for cl in clusterL:
        liL.extend(cl)

    return liL
        
def writeFamilies(liL,fn):
    '''Given a list of islands, write all the families contained within to file, one family per line.'''

    lFamNumL = []
    for liO in liL:
       lFamNumL.extend(liO.locusFamilyL) 

    lFamNumL.sort()
       
    f=open(fn,'w')
    for lfNum in lFamNumL:
        print(lfNum,file=f)
    f.close()

def printClusterCounts(islandsL,tree):

    L=[0 for i in range(trees.nodeCount(tree))]

    for island in islandsL:
        L[island.mrca] += 1

    print(L)
       

    
    
## Main function  
    
def makeLocusIslands(geneOrderT,geneNames,subtreeL,tree,paramD,familiesO,strainStr2NumD,strainNum2StrD, outputSummaryF):
    '''Parallelized wrapper to merge locus islands at different nodes.'''

    numThreads = paramD['numThreads']
    rootFocalClade = paramD['rootFocalClade']
    islandOutFN = paramD['islandOutFN']
    geneProximityRange = paramD['geneProximityRange']
    proximityThresholdMerge1 = paramD['proximityThresholdMerge1']
    rscThresholdMerge1 = paramD['rscThresholdMerge1']
    maxClusterSize = paramD['maxClusterSize']
    
    geneProximityD = genomes.createGeneProximityD(geneOrderT,geneProximityRange )
    locIslByNodeL=createLocIslByNodeL(familiesO,tree)
    numIslandsAtEachNodeAtStartL = [len(L) for L in locIslByNodeL]
    focalNodesL = getFocalNodesInOrderOfNumDescendants(tree,strainStr2NumD,rootFocalClade)

    ##  Merge in clusters

    locusIslandClusterL,singletonClusterL = createLocusIslandClusters(locIslByNodeL,focalNodesL,subtreeL,familiesO,geneProximityD,geneProximityRange,maxClusterSize)

    # create argumentL to be passed to p.map and mergeLocIslandsAtNode
    argumentL = []
    for clusterL in locusIslandClusterL:
        argumentL.append((clusterL,geneProximityD,proximityThresholdMerge1,rscThresholdMerge1,subtreeL[clusterL[0].mrca],familiesO))
    p=Pool(numThreads)
    mergedL = p.map(mergeLocIslandsAtNode, argumentL) # run it

    # update locIslByNodeL with the merged nodes
    locIslByNodeL = updateIslandByNodeLEntries(locIslByNodeL,focalNodesL,mergedL)

    
    ## Family improvement

    # not currently doing this
    
    ##  Merge at mrca nodes
    argumentL = []
    for mrcaNode in focalNodesL:
        argumentL.append((locIslByNodeL[mrcaNode],geneProximityD,proximityThresholdMerge1,rscThresholdMerge1,subtreeL[mrcaNode],familiesO))
    p=Pool(numThreads)
    mergedL = p.map(mergeLocIslandsAtNode, argumentL) # run it

    # add the islands that were identified as singleton clusters
    mergedL.extend(singletonClusterL)
    
    # again update locIslByNodeL
    locIslByNodeL = updateIslandByNodeLEntries(locIslByNodeL,focalNodesL,mergedL)

    numIslandsAtEachNodeAtEndL = [len(L) for L in locIslByNodeL]

    ## Summary and output

    # print summary of merging
    printSummary(focalNodesL,strainNum2StrD,numIslandsAtEachNodeAtStartL,numIslandsAtEachNodeAtEndL,outputSummaryF)
    
    # write islands
    writeIslands(locIslByNodeL,strainNum2StrD,islandOutFN)

    return locIslByNodeL

## Support functions

def createLocIslByNodeL(familiesO,tree):
    '''Create locus islands, one family each. Initially store islands
separately by mrca in a list of lists. (The index of the outer list
corresponds to the mrca)
    '''
    locIslByNodeL=[[] for i in range(trees.nodeCount(tree))]

    for lfO in familiesO.iterLocusFamilies():
        liO = LocusIsland(lfO.locusFamNum, lfO.lfMrca, [lfO.locusFamNum])
        locIslByNodeL[liO.mrca].append(liO)

    # sort each list by island number
    for i in range(len(locIslByNodeL)):
        locIslByNodeL[i].sort(key=lambda x: x.id)
    
    return locIslByNodeL

def getFocalNodesInOrderOfNumDescendants(tree,strainStr2NumD,rootFocalClade):
    '''Get a list of all the nodes in the rootFocalClade. Then sort these
according to the number of leaves descending from them, biggest
first.'''

    focalSubtree = trees.subtree(tree,strainStr2NumD[rootFocalClade])
    focalNodesL = []
    for node in trees.nodeList(focalSubtree):
        # go through every node in the focal clade
        numDescend = trees.leafCount(trees.subtree(tree,node)) # count descendants
        focalNodesL.append((node,numDescend))
    focalNodesL.sort(key=lambda x: x[1],reverse=True) # sort on 2nd pos, biggest first
    # extract and return only the nodes
    return [node for node,numDescend in focalNodesL]

## Cluster formation

def createLocusIslandClusters(locIslByNodeL,focalNodesL,subtreeL,familiesO,geneProximityD,proximityThreshold,maxClusterSize):
    '''For every node in the focal clade, take the set of single family
LocusIslands in locIslByNodeL. Break this up into smaller
clusters based on the chromosomal distances between members of the
familes. Each resulting cluster should contain LocusIslands that we
are likely to merge.'''

    locusIslandClustersL = [] #holds non-singleton clusters 
    singletonClustersL = [] #holds all of the islands from all MRCA nodes that are returned in clusters only containing one island 
    
    #loop through all of the mrcaNode lists 
    for mrcaNode in focalNodesL:

        subtree = subtreeL[mrcaNode]
        islandsAtMrcaNodeL = locIslByNodeL[mrcaNode] 
        
        mrcaClustersL,mrcaSingletonClustersL = createMrcaNodeClusters(islandsAtMrcaNodeL,familiesO,subtree,geneProximityD,proximityThreshold,maxClusterSize)

        singletonClustersL.extend(mrcaSingletonClustersL)
        
        locusIslandClustersL.extend(mrcaClustersL)
    
    return locusIslandClustersL,singletonClustersL

def createMrcaNodeClusters(islandsAtMrcaNodeL,familiesO,subtree,geneProximityD,proximityThreshold,maxClusterSize):
    
    '''Takes in a Mrca node and other node information 
    and clusters the nodes within the mrca node that are likely 
    to merge'''

    mrcaClustersL = []
    mrcaSingletonClustersL = []
    
    while islandsAtMrcaNodeL:

        # clusterL is the ultimate destination for cluster
        # members. onDeckL is where we put islands that will be in the
        # cluster, but which haven't been used as a seed to search for
        # other cluster members yet.
        clusterL = [] 
        onDeckL = [islandsAtMrcaNodeL.pop()]
        
        clusterL,islandsAtMrcaNodeL = populateCluster(clusterL,onDeckL,islandsAtMrcaNodeL,familiesO,subtree,geneProximityD,proximityThreshold,maxClusterSize)
        
        if len(clusterL) > 1:
            mrcaClustersL.append(clusterL)
        else:
            mrcaSingletonClustersL.append(clusterL)

    return mrcaClustersL,mrcaSingletonClustersL


def populateCluster(clusterL,onDeckL,islandsAtMrcaNodeL,familiesO,subtree,geneProximityD,proximityThreshold,maxClusterSize):
    '''Populate clusterL by searching for islands in
islandsAtMrcaNodeL. onDeckL consists of islands that will be added to
clusterL, but which need to be used to search first.

    '''

    while onDeckL:
        
        searchSeedLocIslO = onDeckL.pop()
        # this LocIsl should only have one LocFam
        searchSeedLocFamO = list(searchSeedLocIslO.iterLocusFamilies(familiesO))[0]

        tempFoundL=[]
        for liO in islandsAtMrcaNodeL:
            locFamO = list(liO.iterLocusFamilies(familiesO))[0]

            proxB = proximitySubtree(searchSeedLocFamO,locFamO,geneProximityD,proximityThreshold,subtree)
            if proxB:
                tempFoundL.append(liO)

        # done searching, add to final list
        clusterL.append(searchSeedLocIslO)

        # add the things we found, 1 by 1
        for liO in tempFoundL:
            onDeckL.append(liO)
            islandsAtMrcaNodeL.remove(liO)
            
            if len(clusterL) + len(onDeckL) == maxClusterSize:
                # no more room. Stop now, leaving the rest of
                # tempFoundL in islandsAtMrcaNodeL
                clusterL.extend(onDeckL)
                return clusterL,islandsAtMrcaNodeL

    return clusterL,islandsAtMrcaNodeL
            
            
def populateClusterJacob(islandsAtMrcaNodeL,subtreeL,familiesO,geneProximityD,proximityThreshold,maxClusterSize,mrcaNode, currentCluster):
    '''Takes in a island  and parses 
    though all of the nodes in the mrcaNode that is 
    not already used in another cluster if it is within 
    proximity adds it to newCluster'''
    
    index = 1
    while index<len(islandsAtMrcaNodeL):
        if len(currentCluster) > maxClusterSize:
            break 
            
        subtree = subtreeL[mrcaNode]

        currentFam = familiesO.getLocusFamily(currentCluster[0].locusFamilyL[0])

        comparisonFam = familiesO.getLocusFamily(islandsAtMrcaNodeL[index].locusFamilyL[0])

        proxB = proximitySubtree(currentFam,comparisonFam,geneProximityD,proximityThreshold,subtree)
           
        if proxB: 
            currentCluster.append(islandsAtMrcaNodeL[index])
            islandsAtMrcaNodeL.remove(islandsAtMrcaNodeL[index])
        else:
            index+=1
        
def proximitySubtree(lfam0,lfam1,geneProximityD,proximityThreshold,subtree):
    '''Given two gene families with the same mrcaNode, return boolean
indicating whether any of their genes are within proximityThreshold of
each other.
    '''
    if subtree[1] == ():
        return proximity(lfam0,lfam1,geneProximityD,proximityThreshold,subtree[0])
    else:
        left = proximitySubtree(lfam0,lfam1,geneProximityD,proximityThreshold,subtree[1])
        right = proximitySubtree(lfam0,lfam1,geneProximityD,proximityThreshold,subtree[2])
        return left or right

def updateIslandByNodeLEntries(locIslByNodeL,focalNodesL,mergedL):
    '''Given a list mergedL containing merged clusters of LocusIslands,
put back in locIslByNodeL. mergedL clusters all have mrca within
focalNodesL. We first blank the corresponding mrca location in
locIslByNodeL, then add the contents of mergedL.'''
    
    # blank out the entries in locIslByNodeL which are within the root focal clade
    for mrcaNode in focalNodesL:
        locIslByNodeL[mrcaNode] = []

    # fill them with LocusIslands from mergedL
    for clusterL in mergedL:
        locIslByNodeL[clusterL[0].mrca].extend(clusterL)

    return locIslByNodeL
    
## Iterative merging

def mergeLocIslandsAtNode(argT):
    '''Given a list of locus islands at one node (locusIslandL)
iteratively merge until there are no more pairwise scores above
threshold. rscThreshold represents the threshold below which we no
longer merge islands.
    '''

    locusIslandL,geneProximityD,proximityThreshold,rscThreshold,subtree,familiesO = argT
    
    if len(locusIslandL) < 2:
        # nothing to merge
        return locusIslandL

    # Pre-calculate costDiff scores between all families in locusIslandL
    lFamNumL = []
    for liO in locusIslandL:
        lFamNumL.extend(liO.locusFamilyL)
    costDiffD = costDiffDict((lFamNumL,familiesO,geneProximityD,proximityThreshold,subtree))
    
    # create initial scoreD
    scoreD = createScoreD(locusIslandL,costDiffD)

    # Merge
    while True:
        sc,locIslandPairT,orientation=maxScore(scoreD)
        if sc < rscThreshold:
            break

        ind0,li0 = searchLocIslandsByID(locusIslandL,locIslandPairT[0])
        ind1,li1 = searchLocIslandsByID(locusIslandL,locIslandPairT[1])

        li0.merge(li1,orientation)

        # delete li1
        del locusIslandL[ind1]

        # remove all scores in scoreD that involve li0 or li1
        delScores(scoreD,li0.id,li1.id)

        # calculate new scores for li0 against all other islands
        addScores(scoreD,li0,locusIslandL,costDiffD)

    return locusIslandL

def maxScore(scoreD):
    '''Find the entry with the highest score in scoreD, and return the
corresponding key.'''
    bestSc=-float('inf')
    bestLocIslandPairT=()
    bestOrientation = 0
    for locIslandPairT,(sc,orientation) in scoreD.items():
        if sc > bestSc:
            bestSc=sc
            bestLocIslandPairT = locIslandPairT
            bestOrientation = orientation
    return bestSc,bestLocIslandPairT,bestOrientation

def delScores(scoreD,li0ID,li1ID):
    '''Given two locus island ids from newly merged nodes, delete any entries in
score D that come from them.'''
    # find ones to delete
    toDelL=[]
    for key in scoreD.keys():
        if li0ID in key or li1ID in key:
            toDelL.append(key)

    # now delete them
    for key in toDelL:
        del scoreD[key]

def addScores(scoreD,li0,locusIslandL,costDiffD):
    '''Get scores for locus island li0 against all other locus islands and add to
scoreD.'''
    for locIsl in locusIslandL:
        if locIsl.id != li0.id:
            storeScore(li0,locIsl,costDiffD,scoreD)

def searchLocIslandsByID(listOfLocIslands,id):
    '''Search for a locus island with id equal to id. Return the index of the
first we find, and None if their isn't one.
    '''
    for i,isl in enumerate(listOfLocIslands):
        if isl.id == id: return i,isl
    return None,None

## Scoring

def costDiffDict(argT):
    '''Create a dictionary of costDiff scores between all pairs of locus
families in lFamNumL.'''

    lFamNumL,familiesO,geneProximityD,proximityThreshold,subtree=argT
    
    cdD={}
    for i in range(len(lFamNumL)-1):
        lf1 = familiesO.getLocusFamily(lFamNumL[i])
        for j in range(i+1,len(lFamNumL)):
            lf2 = familiesO.getLocusFamily(lFamNumL[j])
            cdsc = costDiff(lf1,lf2,geneProximityD,proximityThreshold,subtree)
            cdD[(lf1.locusFamNum,lf2.locusFamNum)] = cdsc
            cdD[(lf2.locusFamNum,lf1.locusFamNum)] = cdsc
    return cdD

def costDiff(lfam1,lfam2,geneProximityD,proximityThreshold,subtree):
    '''Given two families calculate the difference in rcost depending on
whether we assume the root is not proximate or proximate. lfam1 and
lfam2 are family tuples specifying the genes present in a family.
    '''
    t=rcost(lfam1,lfam2,geneProximityD,proximityThreshold,subtree,True)
    f=rcost(lfam1,lfam2,geneProximityD,proximityThreshold,subtree,False)
    return(f-t)

def createScoreD(locusIslandL,costDiffD):
    '''Create dictionary of scores between all locus islands at a single node
(and thus with the same mrca).'''
    scoreD={}
    for i in range(len(locusIslandL)-1):
        for j in range(i+1,len(locusIslandL)):
            storeScore(locusIslandL[i],locusIslandL[j],costDiffD,scoreD)
    return scoreD

def storeScore(li0,li1,costDiffD,scoreD):
    '''Calculate and store score in scoreD. We follow convention that key
in scoreD should always have the lower island id first.'''
    if li0.id < li1.id:
        key = li0.id,li1.id
        score,orientation=rscore(li0,li1,costDiffD)
        # rscore returns different things depending on order
        # so we must be consistent with what we do in key.
    else:
        key = li1.id,li0.id
        score,orientation=rscore(li1,li0,costDiffD)
        
    scoreD[key]=(score,orientation)
    
def proximity(lfam1,lfam2,geneProximityD,proximityThreshold,strain):
    '''Return True if any of the genes at strain from lfam1 are within
proximityThreshold of genes at that strain for lfam2. proximityThreshold
is measured in genes, e.g. 1 means the adjacent gene.
    '''
    for gn1 in lfam1.iterGenesByStrain(strain):
        for gn2 in lfam2.iterGenesByStrain(strain):
            if gn1<gn2: key = (gn1,gn2)
            else: key = (gn2,gn1)
            if key in geneProximityD and geneProximityD[key] <= proximityThreshold:
                return True
    return False
  
def rcost(lfam1,lfam2,geneProximityD,proximityThreshold,subtree,rootProximate):
    '''Parsimony based calculation of cost of evolutionary rearrangement
given lfam1 and lfam2 begin at root of subtree. Assume either proximate
(nearby) or not at root (specificed by rootProximate). Charge 1 for
each rearrangment.
    '''
    if subtree[1]==():
        prox=proximity(lfam1,lfam2,geneProximityD,proximityThreshold,subtree[0])
        if (prox and rootProximate) or (not prox and not rootProximate):
            # state given by rootProximate matches adjacency info in our data
            return 0
        else:
            return 1
    else:
        # left subtree
        left = rcost(lfam1,lfam2,geneProximityD,proximityThreshold,subtree[1],rootProximate)
        chLeft = 1 + rcost(lfam1,lfam2,geneProximityD,proximityThreshold,subtree[1],not rootProximate)

        # right subtree
        right = rcost(lfam1,lfam2,geneProximityD,proximityThreshold,subtree[2],rootProximate)
        chRight = 1 + rcost(lfam1,lfam2,geneProximityD,proximityThreshold,subtree[2],not rootProximate)

        return min(left,chLeft) + min(right,chRight)

def rscore(li0,li1,costDiffD):
    '''Returns rearrangement score and orientation between LocusIslands
li0 and li1. Considers all four ways these locus islands could join
(since there are two locus islands each with two ends). This score is
the rcost given we start not proximate minus the rcost given we start
proximate. costDiffD is the precomputed cost diff scores between
families. orientation is an number 0-3 indicating which merge
orientation the (best) score came from.

    '''
    if li0.mrca != li1.mrca:
        return -float('inf')
    else:
        # we try combining in each of the 4 orientations (but if locus
        # island only has 1 family, then we can skip the reverse
        # orientation for that one.
        caseL = [-float('inf')]*4
        
        # case 0: last lfam in li0 vs. first lfam in li1
        caseL[0] = costDiffD[(li0.locusFamilyL[-1],li1.locusFamilyL[0])]

        # case 1: last lfam in li0 vs. last lfam in li1
        if len(li1.locusFamilyL) == 1:
            caseL[1] = caseL[0] # since first and last of li1 are same
        else:
            caseL[1] = costDiffD[(li0.locusFamilyL[-1],li1.locusFamilyL[-1])]
            
        # case 2: first lfam in li0 vs. first lfam in li1
        if len(li0.locusFamilyL) == 1:
            caseL[2] = caseL[0] # since first and last of li0 are same
        else:
            caseL[2] = costDiffD[(li0.locusFamilyL[0],li1.locusFamilyL[0])]
            
        # case 3: first lfam in li0 vs. last lfam in li1
        if len(li0.locusFamilyL) == 1 and len(li1.locusFamilyL) > 1:
            caseL[3] = caseL[1]
        elif len(li0.locusFamilyL) > 1 and len(li1.locusFamilyL) == 1:
            caseL[3] = caseL[2]
        elif len(li0.locusFamilyL) == 1 and len(li1.locusFamilyL) == 1:
            caseL[3] = caseL[0]
        else: # both longer than 1
            caseL[3] = costDiffD[(li0.locusFamilyL[0],li1.locusFamilyL[-1])]            

        score = max(caseL)
        orientation = caseL.index(score)
        
        return score,orientation

## Output

def printSummary(focalNodesL,strainNum2StrD,numIslandsAtEachNodeAtStartL,numIslandsAtEachNodeAtEndL,outputSummaryF):
    '''Print a summary of the merging saying how many islands there were
at each node in the focal clade, before and after merging.'''

    print("Number of islands per node in focal clade: ",file=outputSummaryF)
    rowL=[]
    rowL.append(['Node','Before merge','After merge'])
    rowL.append(['----','------------','-----------'])
    for mrcaNode in focalNodesL:

        rowL.append([strainNum2StrD[mrcaNode],str(numIslandsAtEachNodeAtStartL[mrcaNode]),str(numIslandsAtEachNodeAtEndL[mrcaNode])])
    
    analysis.printTable(rowL,indent=2,fileF=outputSummaryF)

    return

def writeIslands(locIslByNodeL,strainNum2StrD,islandOutFN):
    '''Write the islands to a file'''
    f=open(islandOutFN,"w")
    for branch in range(len(locIslByNodeL)):
        for island in locIslByNodeL[branch]:
            print(island.fileStr(strainNum2StrD),file=f)
    f.close()


def readIslands(islandFN,tree,strainStr2NumD):
    '''Given a file name for a islands output file, load back
recreating locIslByNodeL.'''

    locIslByNodeL=[[] for i in range(trees.nodeCount(tree))]
    
    f=open(islandFN,'r')
    while True:
        s=f.readline()
        if s == '':
            break
        gr=str2Island(s.rstrip(),strainStr2NumD)
        locIslByNodeL[gr.mrca].append(gr)
    f.close()

    return locIslByNodeL

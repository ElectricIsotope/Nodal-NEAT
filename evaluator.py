from multiprocessing import Pool
from functools import partial
import logging
import random as rand
from genome import genome
from innovation import globalConnections
from nuclei import nuclei

# DEFAULT FITNESS FUNCTION:
# evaluate xor.. for debugging, dont let this turn into ROM/POM, build at least 2-3 test cases asap before feature addition

# TODO: make a seperate NEAT package that is called in PoM/RoM. this allows seperate versioning :)
# TODO: branch this off into a NEAT algorithm and PoM/RoM so PoM/RoM can be selectively merged with NEAT updates
# TODO: how to make this safe for parallelism (e.g.: a connection is discovered in two seperate genomes concurrently.)
#               how can this be interrupt handled post-generation?
# TODO: Dask
# TODO: add verbosity levels with logging for tracing at each level of encapsulation
# TODO: can networkx be used for forward propagation given associative matrix?
# TODO: implement this in Cython


class evaluator:
    # TODO: pass in inheritance rates (addNodeFitParent, addNodeLesserParent, (and possibly: addConnectionFitParent, addConnectionLesserParent))
    # TODO: this is just inherit more/less connection since missing a connection prevents all subsequent splits
    # TODO: !DOCSTRING!
    # TODO: parallelize everything!
    def __init__(self, inputs, outputs, population, connectionMutationRate, nodeMutationRate, weightMutationRate, weightPerturbRate, selectionPressure):
        # hyper parameters
        self.connectionMutationRate = connectionMutationRate
        self.nodeMutationRate = nodeMutationRate
        self.weightMutationRate = weightMutationRate
        self.weightPerturbRate = weightPerturbRate
        self.selectionPressure = selectionPressure

        # mutate self.innovation and self.nodeId in innovation.globalConnections
        self.globalInnovations = globalConnections()
        self.nuclei = nuclei()

        genepool = []
        # TODO: initialize in parallel and cleanup initial method
        for entry in range(0, population):
            logging.info('EVALUATOR: building a genome in genepool')
            genepool.append(
                genome.initial(inputs, outputs, self.globalInnovations))
        self.genepool = genepool
        logging.info('EVALUATOR: done constructing evaluator')

    def nextGeneration(self, fitnessFunction):
        '''
        step forward one generation. Processes each genome with the given 
        fitnessFunction and Crosses over members of current genome, selecting parents
        biased to fitness.

        PARAMETERS:
            fitnessFunction: a pure function to be evaluated against each genome. 
                                      MUST take a genome and return a float (fitness score)
        RETURNS:
            None, sets self.genepool to next generation offspring (no elitism crossover)
        '''
        # TODO: continuously evaluate fitness
        # TODO: evaluate genepool for fitness at end of generation
        for ge in self.genepool:
            ge.fitness = fitnessFunction(ge)

        print(max([x.fitness for x in self.genepool]))

        assert all([x.fitness is not None for x in self.genepool]), \
            "missed fitness assignment in evaluator"

        nextPool = []
        swimmers = Pool()
        cross = partial(self.nuclei.crossover,
                        globalInnovations=self.globalInnovations)
        biasFitnessSelect = sorted(
            [x for x in self.genepool], key=lambda x: x.fitness, reverse=True)

        self.nuclei.resetPrimalGenes()
        # @DEPRECATED
        # for ge in biasFitnessSelect:
        #     self.nuclei.readyPrimalGenes(ge)

        while len(nextPool) < len(self.genepool):
            parent1, parent2 = [], []

            for x in range(0, len(self.genepool) - len(nextPool)):
                parent1.append(
                    self.genepool[self.selectBiasFitness(self.selectionPressure)])
                # NOTE: crosses over with self
                parent2.append(
                    self.genepool[self.selectBiasFitness(self.selectionPressure)])

            rawNextPool = swimmers.starmap(
                cross, zip(parent1, parent2))

            for x in rawNextPool:
                if len(nextPool) == len(self.genepool):
                    break
                else:
                    nextPool.append(x)
            for child in nextPool:
                self.mutations(child)

        self.genepool.clear()
        self.genepool = nextPool.copy()
        print('new genepool with {} members'.format(len(self.genepool)))
        nextPool.clear()

        swimmers.close()
        return self.genepool

    def mutations(self, child):
        child.addNodeMutation(
            self.nodeMutationRate, self.globalInnovations)
        child.addConnectionMutation(
            self.connectionMutationRate, self.globalInnovations)
        child.mutateConnectionWeights(
            self.weightMutationRate, self.weightPerturbRate)

    def selectBiasFitness(self, bias):
        '''
        get a genome selection index.

        PARAMETERS:
            bias: an integer for the level of bias for selecting for fitness
        RETURNS:
            selection: an index in genepool list
        '''
        # TODO: very small chance of collision
        selection = rand.randint(0, len(self.genepool))

        for _ in range(0, bias):
            selection = selection - rand.randint(0, selection)
        return selection

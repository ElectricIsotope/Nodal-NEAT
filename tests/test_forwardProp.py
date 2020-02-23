from organisms.evaluator import evaluator
import unittest

class TestForwardProp(unittest.TestCase):
    def test_forwardProp(self):
        print('\n TESTING FORWARD PROPAGATION ')
        eval = evaluator(inputs=2, outputs=2, population=100,
        connectionMutationRate=0.3, nodeMutationRate=0.01,weightMutationRate=0.5,
        weightPerturbRate=0.9,selectionPressure=11)
        test = eval.genepool[0]
        for _ in range(0,20):
            test.addConnectionMutation(eval.connectionMutationRate, eval.globalInnovations)
            test.addNodeMutation(eval.connectionMutationRate, eval.globalInnovations)
            test.mutateConnectionWeights(eval.weightMutationRate, eval.weightPerturbRate)
            
        print('beginning forward propagation')
        vals = [1,2]
        for x in range(0,10):
            outputs = test.forwardProp(vals)
            print('{} Forward Prop of {} produced {}'.format(x, vals, outputs))

if __name__=='__main__':
    unittest.main()
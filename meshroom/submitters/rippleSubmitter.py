import os

# meshroom modules
from meshroom.core.desc import Level
from meshroom.core.submitter import BaseSubmitter

# mpc logging import
# import mpc.logging

# Ripple imports
from mpc.ripple.rippleProcess import RippleProcess
from mpc.ripple.dispatcher import DefaultDispatcher
from mpc.ripple.rippleUtilities import RippleGroup
from mpc.ripple.rippleAttribute import RippleAttribute
# from mpc.ripple.rippleConfig import RippleConfig as _RippleConfig
# from mpc.ripple.rippleStorage import RippleStorage

# validators for numbers
from mpc.pyCore.validators import IntValidator

# _log = mpc.logging.getLogger()

currentDir = os.path.dirname(os.path.realpath(__file__))
binDir = os.path.dirname(os.path.dirname(os.path.dirname(currentDir)))


# Give access to min/maxProcessors, which is an alias to slots
class RippleProcessWithSlots(RippleProcess):
    minProcessors = RippleAttribute('', IntValidator(), 1, True)
    maxProcessors = RippleAttribute('', IntValidator(), 1, True)


class RippleSubmitter(BaseSubmitter):

    reqPackages = []

    def __init__(self, parent=None):
        super(RippleSubmitter, self).__init__(name='Ripple', parent=parent)

        if 'REZ_REQUEST' in os.environ:
            packages = os.environ.get('REZ_REQUEST', '').split()
            resolvedPackages = os.environ.get('REZ_RESOLVE', '').split()
            resolvedVersions = {}
            for r in resolvedPackages:
                # remove implicit packages
                if r.startswith('~'):
                    continue
                # logging.info('REZ: {}'.format(str(r)))
                v = r.split('-')
                # logging.info('    v: {}'.format(str(v)))
                if len(v) == 2:
                    resolvedVersions[v[0]] = v[1]
            for p in packages:
                if p.startswith('~'):
                    continue
                v = p.split('-')
                self.reqPackages.append(
                    '-'.join([v[0], resolvedVersions[v[0]]]))
            # logging.debug('REZ Packages: {}'.format(str(self.reqPackages)))

    def createTask(self, meshroomFile, node, parents):

        nbBlocks = 1

        # Map meshroom GPU modes to MPC services
        gpudict = {
            "NONE": "",
            "NORMAL": ",gpu8G",
            "INTENSIVE": ",gpu16G"
        }

        # decide if we need multiple slots
        minProcessors = 1
        maxProcessors = 1
        if Level.INTENSIVE in (node.nodeDesc.ram, node.nodeDesc.cpu):
            # at least 2 slots
            minProcessors = 2
            # if more than 2 are available without waiting, use 3 or 4
            maxProcessors = 4
        elif Level.NORMAL in (node.nodeDesc.ram, node.nodeDesc.cpu):
            # if 2 are available, otherwise 1
            maxProcessors = 2

        # Specify some constraints
        requirements = "!\"rs*\",@.mem>25{gpu}".format(
            gpu=gpudict[node.nodeDesc.gpu.name])

        # specify which node to wait before launching the current one
        waitsFor = []
        for parent in parents:
            waitsFor.append(parent.name)

        #  execCmd
        python = '/s/apps/users/multiview/bin/rez env {} -- python3'.format(
            " ".join(self.reqPackages))
        # Basic command line for this node
        command = '/s/apps/users/multiview/bin/rez env {rezPackages} -- meshroom_compute --node {nodeName} "{meshroomFile}" --extern'.format(
            rezPackages=" ".join(self.reqPackages),
            nodeName=node.name,
            meshroomFile=meshroomFile)

        if node.isParallelized:
            _, _, nbBlocks = node.nodeDesc.parallelization.getSizes(node)

            # Create as many process as iteration (or chunks)
            rippleprocs = []
            for iteration in range(0, nbBlocks):

                # Add iteration number
                commandext = '{cmd} --iteration {iter}'.format(
                    cmd=command, iter=iteration)

                # Create process task with parameters
                rippleproc = RippleProcessWithSlots(
                    name='{name} iteration {iter}'.format(
                        name=node.name, iter=iteration),
                    execCmd=python,
                    discipline='meshroom',
                    appendKeys=True,
                    keys=requirements,
                    label='{name} iteration {iter}'.format(
                        name=node.name, iter=iteration),
                    cmdList=[commandext],
                    waitsFor=waitsFor,
                    minProcessors=minProcessors,
                    maxProcessors=maxProcessors
                )
                rippleprocs.append(rippleproc)

            rippleObj = RippleGroup(
                label="{name} Group".format(name=node.name),
                execCmd=python,
                discipline='meshroom',
                tasks=rippleprocs,
                name=node.name,
                waitsFor=waitsFor
            )
        else:
            rippleObj = RippleProcessWithSlots(
                name=node.name,
                execCmd=python,
                discipline='meshroom',
                appendKeys=True,
                keys=requirements,
                label=node.name,
                cmdList=[command],
                waitsFor=waitsFor,
                minProcessors=minProcessors,
                maxProcessors=maxProcessors
            )

        return rippleObj

    def submit(self, nodes, edges, filepath, submitLabel="{projectName}"):

        projectName = os.path.splitext(os.path.basename(filepath))[0]
        label = submitLabel.format(projectName=projectName)

        # Build a tree
        tree = {}
        for node in nodes:
            tree[node] = []

        for end, start in edges:
            tree[end].append(start)

        nodesDone = set()
        hasChange = True
        tasks = []

        # As long as a valid node was found in the previous iteration
        while hasChange:

            hasChange = False
            toRemove = []

            # Loop over all nodes in the graph
            for node in tree.keys():

                # Ignore a node already processed
                found = False
                if node.name in nodesDone:
                    found = True

                if found:
                    continue

                # Check if all parents are already visited
                valid = True
                for parent in tree[node]:
                    found = False
                    if parent.name in nodesDone:
                        found = True
                    if found is False:
                        valid = False

                if valid is False:
                    continue

                tasks.append(self.createTask(filepath, node, tree[node]))

                toRemove.append(node.name)
                hasChange = True

            for itemRemove in toRemove:
                nodesDone.add(itemRemove)

        if (len(tasks) == 0):
            return True

        DefaultDispatcher(label=label, tasks=tasks,
                          jobType='release', paused=False)()

        return True

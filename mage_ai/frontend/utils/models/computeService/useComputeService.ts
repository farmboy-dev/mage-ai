import { useCallback, useMemo } from 'react';
import ComputeServiceType, { ComputeServiceUUIDEnum } from '@interfaces/ComputeServiceType';
import useProject from '@utils/models/project/useProject';

function useComputeService(_options: {
  clustersRefreshInterval?: number;
  computeServiceRefreshInterval?: number;
  connectionsRefreshInterval?: number;
  includeAllStates?: boolean;
  pauseFetch?: boolean;
} = {}) {
  const { project, fetchProjects } = useProject();
  const computeService: ComputeServiceType = useMemo(() =>
    Object.keys(project?.spark_config || {}).length ? {
      uuid: ComputeServiceUUIDEnum.STANDALONE_CLUSTER,
      connection_credentials: [],
      setup_steps: [],
    } : null, [project?.spark_config]);
  const fetchAll = useCallback(async () => fetchProjects(), [fetchProjects]);
  return {
    computeService,
    computeServiceUUIDs: { STANDALONE_CLUSTER: ComputeServiceUUIDEnum.STANDALONE_CLUSTER },
    setupComplete: !!computeService,
    fetchAll,
    activeCluster: null,
    clusters: [],
    clustersLoading: false,
    connections: [],
    connectionsLoading: false,
    fetchComputeClusters: fetchAll,
  };
}

export default useComputeService;

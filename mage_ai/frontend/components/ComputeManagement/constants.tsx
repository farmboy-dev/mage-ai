import { BlockCubePolygon, Monitor } from '@oracle/icons';
import FlexContainer from '@oracle/components/FlexContainer';
import Spacing from '@oracle/elements/Spacing';
import Text from '@oracle/elements/Text';
import { pluralize } from '@utils/string';
import AWSEMRClusterType from '@interfaces/AWSEMRClusterType';
import ComputeConnectionType from '@interfaces/ComputeConnectionType';
import ComputeServiceType from '@interfaces/ComputeServiceType';
import { DiamondGem, Settings } from '@oracle/icons';
import { ComputeServiceUUIDEnum } from '@interfaces/ComputeServiceType';
import { SparkConfigType } from '@interfaces/ProjectType';
import { SparkApplicationType, SparkJobType } from '@interfaces/SparkType';
import { TripleBoxes } from '@oracle/icons';
import { UNIT } from '@oracle/styles/units/spacing';

const ICON_SIZE = 8 * UNIT;

export interface TabType {
  Icon: any;
  renderStatus?: (opts?: {
    applications?: SparkApplicationType[];
    applicationsLoading?: boolean;
    clusters?: AWSEMRClusterType[];
    clustersLoading?: boolean;
    computeConnections?: ComputeConnectionType[];
    computeService: ComputeServiceType;
    jobs?: SparkJobType[];
    jobsLoading?: boolean;
  }) => any;
  uuid: string;
}

export type ObjectAttributesType = {
  remote_variables_dir?: string;
  spark_config?: SparkConfigType;
};

export const ComputeServiceEnum = { ...ComputeServiceUUIDEnum };
export type ComputeServiceEnum = typeof ComputeServiceEnum;

export enum MainNavigationTabEnum {
  CLUSTERS = 'clusters',
  MONITORING = 'monitoring',
  RESOURCES = 'resources',
  SETUP = 'setup',
  SYSTEM = 'system',
}

export enum JarFileConfigEnum {
  SPARK = 'spark_config',
}

export const MAIN_NAVIGATION_TAB_DISPLAY_NAME_MAPPING = {
  [MainNavigationTabEnum.CLUSTERS]: 'Clusters',
  [MainNavigationTabEnum.RESOURCES]: 'Resources',
  [MainNavigationTabEnum.MONITORING]: 'Monitoring',
  [MainNavigationTabEnum.SETUP]: 'Setup',
  [MainNavigationTabEnum.SYSTEM]: 'System',
};

export const COMPUTE_SERVICE_DISPLAY_NAME = {

  [ComputeServiceEnum.STANDALONE_CLUSTER]: 'Standalone cluster',
};

export const COMPUTE_SERVICE_KICKER = {

  [ComputeServiceEnum.STANDALONE_CLUSTER]: 'Spark',
};

export const COMPUTE_SERVICE_RENDER_ICON_MAPPING = {

  [ComputeServiceEnum.STANDALONE_CLUSTER]: (
    size: number = ICON_SIZE,
  ) => <TripleBoxes size={size} warning />
};

export const COMPUTE_SERVICES: {
  buildPayload: (data?: ObjectAttributesType) => ObjectAttributesType;
  displayName: string;
  documentationHref: string;
  kicker: string;
  renderIcon: () => any;
  uuid: string;
}[] = [{
    buildPayload: (data: ObjectAttributesType) => ({
      spark_config: {
        app_name: '',
        spark_master: 'local',
        ...data?.spark_config,
      },
    }),
    displayName: COMPUTE_SERVICE_DISPLAY_NAME[ComputeServiceEnum.STANDALONE_CLUSTER],
    documentationHref: 'https://docs.mage.ai/integrations/spark-pyspark#standalone-spark-cluster',
    kicker: COMPUTE_SERVICE_KICKER[ComputeServiceEnum.STANDALONE_CLUSTER],
    renderIcon: COMPUTE_SERVICE_RENDER_ICON_MAPPING[ComputeServiceEnum.STANDALONE_CLUSTER],
    uuid: ComputeServiceEnum.STANDALONE_CLUSTER,
  }];

export const SHARED_TEXT_PROPS: {
  default: boolean;
  monospace: boolean;
  preWrap: boolean;
  small: boolean;
} = {
  default: true,
  monospace: true,
  preWrap: true,
  small: true,
};

export function buildTabs(computeService: ComputeServiceType): TabType[] {
  let arr: TabType[] = [
    {
      Icon: Settings,
      uuid: MainNavigationTabEnum.SETUP,
    },
    {
      Icon: DiamondGem,
      uuid: MainNavigationTabEnum.RESOURCES,
    },
  ];

  if ([
    ComputeServiceUUIDEnum.STANDALONE_CLUSTER,
  ].includes(computeService?.uuid)) {
    // @ts-ignore
    arr.push(...[
      {
        Icon: Monitor,
        renderStatus: ({
          applications,
          applicationsLoading,
          jobs,
          jobsLoading,
        }) => {
          if (applicationsLoading) {
            return null;
          }

          return (
            <FlexContainer flexDirection="column" justifyContent="flex-end" style={{ flexShrink: 0 }}>
              <Text default monospace noWrapping rightAligned xsmall>
                {pluralize('application', applications?.length || 0)}
              </Text>

              <div style={{ marginBottom: UNIT / 2 }} />

              <Text default monospace noWrapping rightAligned xsmall>
                {pluralize('job', jobs?.length || 0)}
              </Text>
            </FlexContainer>
          );
        },
        uuid: MainNavigationTabEnum.MONITORING,
      },
      {
        Icon: BlockCubePolygon,
        uuid: MainNavigationTabEnum.SYSTEM,
      },
    ]);
  }

  return arr;
}

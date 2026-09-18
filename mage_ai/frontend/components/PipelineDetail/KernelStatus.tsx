import { useContext, useEffect, useMemo, useRef, useState } from 'react';
import { ThemeContext } from 'styled-components';
import { useRouter } from 'next/router';
import BlockType from '@interfaces/BlockType';
import Circle from '@oracle/elements/Circle';
import ClickOutside from '@oracle/components/ClickOutside';
import ErrorsType from '@interfaces/ErrorsType';
import Flex from '@oracle/components/Flex';
import FlexContainer from '@oracle/components/FlexContainer';
import FlyoutMenu from '@oracle/components/FlyoutMenu';
import KeyboardShortcutButton from '@oracle/elements/Button/KeyboardShortcutButton';
import PipelineType, { PipelineTypeEnum, PIPELINE_TYPE_DISPLAY_NAME, PIPELINE_TYPE_TO_KERNEL_NAME } from '@interfaces/PipelineType';
import PopupMenu from '@oracle/components/PopupMenu';
import Spacing from '@oracle/elements/Spacing';
import Spinner from '@oracle/components/Spinner';
import api from '@api';
import dark from '@oracle/styles/themes/dark';
import useComputeService from '@utils/models/computeService/useComputeService';
import useKernel from '@utils/models/kernel/useKernel';
import usePrevious from '@utils/usePrevious';
import useProject from '@utils/models/project/useProject';
import { PowerOnOffButton } from '@oracle/icons';
import { LOCAL_STORAGE_KEY_HIDE_KERNEL_WARNING, get, set } from '@storage/localStorage';
import { PADDING_UNITS, UNIT } from '@oracle/styles/units/spacing';
import { SparkApplicationType } from '@interfaces/SparkType';
import { ThemeType } from '@oracle/styles/themes/constants';
import { useKeyboardContext } from '@context/Keyboard';
import { useModal } from '@context/Modal';

type KernelStatusProps = {
  children?: any;
  isBusy: boolean;
  pipeline: PipelineType;
  restartKernel: () => void;
  savePipelineContent: () => void;
  setErrors: (errors: ErrorsType) => void;
  setRunningBlocks: (blocks: BlockType[]) => void;
  updatePipelineMetadata: (name: string, type?: string) => void;
};

function KernelStatus({
  children,
  isBusy,
  pipeline,
  restartKernel,
  savePipelineContent,
  setErrors,
  setRunningBlocks,
  updatePipelineMetadata,
}: KernelStatusProps) {
  const router = useRouter();
  const { kernel } = useKernel({ pipelineType: pipeline?.type });
  const {
    featureEnabled,
    featureUUIDs,
    sparkEnabled,
  } = useProject();
  const {
    activeCluster,
    clusters,
    clustersLoading,
    computeService,
    computeServiceUUIDs,
    connections,
    connectionsLoading,
    fetchAll,
    fetchComputeClusters,
    setupComplete,
  } = useComputeService({
    clustersRefreshInterval: 5000,
    computeServiceRefreshInterval: 5000,
    connectionsRefreshInterval: 5000,
    pauseFetch: !sparkEnabled,
  });

  const themeContext: ThemeType = useContext(ThemeContext);
  const {
    alive,
    usage,
  } = kernel || {};
  const [showSelectCluster, setShowSelectCluster] = useState(false);
  const [showSelectKernel, setShowSelectKernel] = useState(false);
  const [clusterSelectionVisible, setClusterSelectionVisible] = useState(false);
  const [computeConnectionVisible, setComputeConnectionVisible] = useState(false);

  const refSelectKernel = useRef(null);

  // TODO (tommy dang): how do we make this dynamic based on the cloud provider they choose?

  const {
    data: dataSparkApplications,
  } = api.spark_applications.list({}, {}, {
    pauseFetch: !sparkEnabled,
  });
  const sparkApplications: SparkApplicationType[] =
    useMemo(() => dataSparkApplications?.spark_applications, [
      dataSparkApplications,
    ]);

  const uuidKeyboard = 'KernelStatus';
  const {
    registerOnKeyDown,
    unregisterOnKeyDown,
  } = useKeyboardContext();

  useEffect(() => () => {
    unregisterOnKeyDown(uuidKeyboard);
  }, [unregisterOnKeyDown, uuidKeyboard]);

  const kernelPid = useMemo(() => usage?.pid, [usage?.pid]);
  const kernelPidPrevious = usePrevious(kernelPid);

  const [showKernelWarning, hideKernelWarning] = useModal(() => (
    <PopupMenu
      cancelText="Close"
      centerOnScreen
      confirmText="Don't show again"
      neutral
      onCancel={hideKernelWarning}
      onClick={() => {
        set(LOCAL_STORAGE_KEY_HIDE_KERNEL_WARNING, 1);
        hideKernelWarning();
      }}
      subtitle={
        'You may need to refresh your page to continue using the notebook. Unexpected ' +
        'kernel restarts may be caused by your kernel running out of memory.'
      }
      title="The kernel has restarted"
      width={UNIT * 34}
    />
  ), {}, [], {
    background: true,
    uuid: 'restart_kernel_warning',
  });

  useEffect(() => {
    const hide = get(LOCAL_STORAGE_KEY_HIDE_KERNEL_WARNING, 0);
    if (kernelPid && kernelPidPrevious && kernelPid !== kernelPidPrevious && isBusy) {
      if (!hide) showKernelWarning();
      setRunningBlocks([]);
    }
  }, [
    isBusy,
    kernelPid,
    kernelPidPrevious,
    setRunningBlocks,
    showKernelWarning,
  ]);

  const validComputePipelineType = useMemo(() => [
    PipelineTypeEnum.PYTHON,
    PipelineTypeEnum.PYSPARK,
  ].includes(pipeline?.type), [
    pipeline,
  ]);

  const statusIconMemo = useMemo(() => {
    return (
      <Circle
        color={isBusy
          ? (themeContext || dark).borders.info
          : (alive
            ? (themeContext || dark).borders.success
            : (themeContext || dark).borders.danger
          )
        }
        size={UNIT}
      />
    );
  }, [
    alive,
    isBusy,
    themeContext,
  ]);

  const computeStatusMemo = useMemo(() => {
    if (!sparkEnabled || !validComputePipelineType) {
      return null;
    }

    let menuEl;
    let onClick;
    let pipelineDisplayName;
    let statusIconEl;
    const buttonProps: {
      muted?: boolean;
      warning?: boolean;
    } = {
      muted: false,
      warning: false,
    };

    if (computeServiceUUIDs.STANDALONE_CLUSTER === computeService?.uuid) {
      if (!dataSparkApplications) {
        pipelineDisplayName = 'Loading compute';
        statusIconEl = (
          <Spinner
            inverted
            small
          />
        );
      } else if (!sparkApplications?.length) {
        onClick = () => router.push('/compute');
        pipelineDisplayName = 'Compute unavailable';
        statusIconEl = (
          <PowerOnOffButton
            danger
          />
        );
      } else if (sparkApplications?.length >= 1) {
        const sparkApplication = sparkApplications?.[0];

        pipelineDisplayName = [
          sparkApplication?.name,
          sparkApplication?.attempts?.[0]?.app_spark_version,
        ].filter(value => value).join(' ');

        statusIconEl = (
          <PowerOnOffButton
            success
          />
        );
      }
    }

    return (pipelineDisplayName
      ? (
        <div style={{ position: 'relative' }}>
          <KeyboardShortcutButton
            beforeElement={statusIconEl}
            blackBorder
            compact
            inline
            noHover={!dataSparkApplications || sparkApplications?.length >= 1}
            onClick={onClick}
            uuid="Pipeline/ComputeStatus"
            {...buttonProps}
          >
            {pipelineDisplayName}
          </KeyboardShortcutButton>

          {menuEl}
        </div>
      ): null
    );
  }, [
    activeCluster,
    clusterSelectionVisible,
    clusters,
    computeService,
    computeServiceUUIDs,
    dataSparkApplications,
    pipeline,
    router,
    setClusterSelectionVisible,
    setComputeConnectionVisible,
    sparkApplications,
    sparkEnabled,
    validComputePipelineType,
  ]);

  const kernelStatusMemo = useMemo(() => (
    <div
      ref={refSelectKernel}
      style={{
        position: 'relative',
      }}
    >
      <FlexContainer alignItems="center">

        <KeyboardShortcutButton
          beforeElement={statusIconMemo}
          blackBorder
          compact
          inline
          onClick={() => setShowSelectKernel(true)}
          uuid="Pipeline/KernelStatus/kernel"
        >
          {PIPELINE_TYPE_DISPLAY_NAME[pipeline?.type || PipelineTypeEnum.PYTHON]}
        </KeyboardShortcutButton>

        <ClickOutside
          disableEscape
          onClickOutside={() => setShowSelectKernel(false)}
          open={showSelectKernel}
        >
          <FlyoutMenu
            items={[
              {
                isGroupingTitle: true,
                label: () => 'Select kernel',
                uuid: 'select_kernel',
              },
              ...Object.keys(PIPELINE_TYPE_TO_KERNEL_NAME)
                .filter(type => pipeline?.type != type)
                .map(type => ({
                  label: () => PIPELINE_TYPE_DISPLAY_NAME[type] || type,
                  onClick: () => updatePipelineMetadata(pipeline?.name, type),
                  uuid: type,
                })),
            ]}
            onClickCallback={() => setShowSelectKernel(false)}
            open={showSelectKernel}
            parentRef={refSelectKernel}
            rightOffset={0}
            uuid="KernelStatus/select_kernel"
            width={UNIT * 25}
          />
        </ClickOutside>
      </FlexContainer>
    </div>
  ), [alive,
isBusy,
pipeline,
setShowSelectCluster,
setShowSelectKernel,
showSelectCluster,
showSelectKernel,
statusIconMemo,
themeContext,
updatePipelineMetadata]);

  return (
    <FlexContainer
      alignItems="center"
      fullHeight
      justifyContent="space-between"
    >
      <FlexContainer
        alignItems="center"
        fullHeight
        justifyContent="flex-start"
      >
        {children}
      </FlexContainer>

      <Spacing px={PADDING_UNITS}>
        <Flex alignItems="center">
          <FlexContainer alignItems="center">
            {kernelStatusMemo}

            {computeStatusMemo && (
              <Spacing ml={1}>
                {computeStatusMemo}
              </Spacing>
            )}
          </FlexContainer>
        </Flex>
      </Spacing>
    </FlexContainer>
  );
}

export default KernelStatus;

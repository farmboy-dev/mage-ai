import { useCallback, useMemo } from 'react';
import Button from '@oracle/elements/Button';
import FlexContainer from '@oracle/components/FlexContainer';
import KeyValueConfigurationSection from './shared/KeyValueConfigurationSection';
import Link from '@oracle/elements/Link';
import Spacing from '@oracle/elements/Spacing';
import Text from '@oracle/elements/Text';
import { Save } from '@oracle/icons';
import { ComputeServiceUUIDEnum } from '@interfaces/ComputeServiceType';
import { ContainerStyle } from '@components/shared/index.style';
import { ObjectAttributesType } from './constants';
import { SparkConfigType } from '@interfaces/ProjectType';
import { PADDING_UNITS, UNITS_BETWEEN_SECTIONS } from '@oracle/styles/units/spacing';

type ResourceManagementProps = {
  attributesTouched: {
    [key: string]: any;
  }
  isLoading?: boolean;
  mutateObject: (data?: ObjectAttributesType) => void;
  objectAttributes: ObjectAttributesType;
  onCancel?: () => void;
  selectedComputeService?: ComputeServiceUUIDEnum;
  setObjectAttributes: (objectAttributes: ObjectAttributesType) => void;
}

function ResourceManagement({
  attributesTouched,
  isLoading,
  mutateObject,
  objectAttributes,
  onCancel,
  selectedComputeService,
  setObjectAttributes,
}: ResourceManagementProps) {

  const setObjectAttributesSparkConfig =
    useCallback((data: SparkConfigType) => setObjectAttributes({
      spark_config: {
        ...objectAttributes?.spark_config,
        ...data,
      },
    }), [
      objectAttributes,
      setObjectAttributes,
    ]);

  const objectAttributesSparkConfig = useMemo(() => objectAttributes?.spark_config || {}, [
    objectAttributes,
  ]);

  return (
    <ContainerStyle>
      <KeyValueConfigurationSection
        addButtonText="Add Spark configuration"
        addTextInputPlaceholder="e.g. spark.driver.cores"
        alreadyExistsMessage="Spark configuration exists"
        configurationValuePlaceholder="e.g. 4g"
        configurations={objectAttributesSparkConfig?.others}
        createButtonText="Create Spark configuration"
        description={(
          <>
            <Text muted>
              List of key-value pairs to be set in <Text
                inline
                monospace
                muted
              >
                SparkConf
              </Text>, e.g. <Text
                inline
                monospace
                muted
              >
                spark.executor.memory=4g
              </Text>.
            </Text>
            <Text muted>
              For a list of all configurations, see the <Link
                href="https://spark.apache.org/docs/latest/configuration.html"
                inline
                openNewWindow
              >
                Spark configuration documentation
              </Link>.
            </Text>
          </>
        )}
        emptyState="There are currently no executor Spark configurations."
        setConfigurations={data => setObjectAttributesSparkConfig({
          others: data,
        })}
        title="Spark configurations"
      />

      <Spacing mb={UNITS_BETWEEN_SECTIONS} />

      <FlexContainer>
        <Button
          beforeIcon={<Save />}
          disabled={!attributesTouched || !Object.keys(attributesTouched)?.length}
          loading={isLoading}
          onClick={() => mutateObject()}
          primary
        >
          Save changes
        </Button>

        {onCancel && (
          <>
            <Spacing mr={PADDING_UNITS} />

            <Button
              onClick={() => onCancel?.()}
              secondary
            >
              Cancel and go back
            </Button>
          </>
        )}
      </FlexContainer>
    </ContainerStyle>
  );
}

export default ResourceManagement;

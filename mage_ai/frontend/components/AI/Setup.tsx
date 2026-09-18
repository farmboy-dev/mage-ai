import Link from '@oracle/elements/Link';
import Panel from '@oracle/components/Panel';
import Spacing from '@oracle/elements/Spacing';
import Text from '@oracle/elements/Text';
import { UNITS_BETWEEN_SECTIONS } from '@oracle/styles/units/spacing';

export default function Setup() {
  return (
    <Spacing mb={UNITS_BETWEEN_SECTIONS}>
      <Panel>
        <Text warning>
          Configure an OpenAI-compatible API base URL and model in{' '}
          <Link href="/settings/workspace/preferences">project preferences</Link>
          {' '}before generating pipelines. Add an API key only if your internal server requires one.
        </Text>
      </Panel>
    </Spacing>
  );
}

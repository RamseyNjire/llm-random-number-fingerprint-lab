import { mkdirSync, writeFileSync } from 'node:fs';
import { dirname, resolve } from 'node:path';
import { fileURLToPath } from 'node:url';

const here = dirname(fileURLToPath(import.meta.url));
const outputPath = resolve(here, '../workflows/templates/random-number-fingerprint-runner-template.json');
const sheetIdPlaceholder = 'YOUR_GOOGLE_SHEET_ID';

const expandCode = String.raw`function clean(value) {
  return String(value ?? '').trim();
}

function enabled(value) {
  return ['true', 'yes', '1', 'y'].includes(clean(value).toLowerCase());
}

function toNumber(value, fallback) {
  const parsed = Number(value);
  return Number.isFinite(parsed) ? parsed : fallback;
}

const runId = 'rn_' + new Date().toISOString().replace(/[:.]/g, '-');
const outputs = [];
let counter = 0;

for (const item of $input.all()) {
  const row = item.json || {};
  if (!enabled(row.enabled)) continue;

  const repetitions = Math.max(1, Math.min(toNumber(row.repetitions, 1), 10000));
  const seedPolicy = clean(row.seed_policy || 'none').toLowerCase();
  const seedStart = toNumber(row.seed_start, 1);

  for (let i = 1; i <= repetitions; i += 1) {
    counter += 1;
    let seedValue = '';
    if (seedPolicy === 'fixed') seedValue = seedStart;
    if (seedPolicy === 'increment' || seedPolicy === 'changing') seedValue = seedStart + i - 1;

    outputs.push({
      json: {
        run_id: runId,
        sample_id: runId + '_' + String(counter).padStart(6, '0'),
        requested_at_ms: Date.now(),
        case_id: clean(row.case_id),
        model_id: clean(row.model_id),
        provider_label: clean(row.provider_label),
        prompt_id: clean(row.prompt_id),
        prompt_text: clean(row.prompt_text),
        condition_label: clean(row.condition_label || 'model_only'),
        provider_order: clean(row.provider_order),
        allow_fallbacks: clean(row.allow_fallbacks || 'TRUE'),
        require_parameters: clean(row.require_parameters || 'FALSE'),
        provider_ignore: clean(row.provider_ignore),
        temperature: toNumber(row.temperature, 1),
        top_p: toNumber(row.top_p, 1),
        reasoning_effort: clean(row.reasoning_effort),
        max_tokens: Math.max(16, toNumber(row.max_tokens, 16)),
        repetition_index: i,
        seed_policy: seedPolicy,
        seed_value: seedValue,
        notes: clean(row.notes),
      },
    });
  }
}

return outputs;`;

const parseCode = String.raw`function pickText(values) {
  for (const value of values) {
    if (typeof value === 'string' && value.trim()) return value.trim();
    if (value && typeof value === 'object') return JSON.stringify(value);
  }
  return '';
}

function maybeNumber(value) {
  if (value === null || value === undefined || value === '') return null;
  const parsed = Number(value);
  return Number.isFinite(parsed) ? parsed : null;
}

function firstInteger(text) {
  const match = String(text || '').match(/-?\d+/);
  return match ? Number(match[0]) : null;
}

function isPrime(n) {
  if (!Number.isInteger(n) || n < 2) return false;
  for (let i = 2; i * i <= n; i += 1) {
    if (n % i === 0) return false;
  }
  return true;
}

function cleanValue(text) {
  return String(text || '')
    .trim()
    .split(/\r?\n/)[0]
    .replace(/^["']+|["'.,;:!?]+$/g, '')
    .trim();
}

function parseResponse(promptId, responseText) {
  const prompt = String(promptId || '').toLowerCase();
  const raw = cleanValue(responseText);
  const integer = firstInteger(raw);

  if (prompt.includes('option_abcd')) {
    const match = raw.toUpperCase().match(/\b[A-D]\b|^[A-D]/);
    return {
      response_type: 'option_abcd',
      response_value: match ? match[0][0] : raw.toUpperCase(),
      valid_response: Boolean(match),
      response_parse_error: match ? '' : 'No A-D option found',
    };
  }

  if (prompt.includes('letter_a_z')) {
    const match = raw.toUpperCase().match(/\b[A-Z]\b|^[A-Z]/);
    return {
      response_type: 'letter_a_z',
      response_value: match ? match[0][0] : raw.toUpperCase(),
      valid_response: Boolean(match),
      response_parse_error: match ? '' : 'No A-Z letter found',
    };
  }

  if (prompt.includes('year_1900_2099')) {
    const valid = Number.isInteger(integer) && integer >= 1900 && integer <= 2099;
    return {
      response_type: 'year_1900_2099',
      response_value: valid ? String(integer) : raw,
      valid_response: valid,
      response_parse_error: valid ? '' : 'No year from 1900 to 2099 found',
    };
  }

  if (prompt.includes('prime_under_100')) {
    const valid = Number.isInteger(integer) && integer > 1 && integer < 100 && isPrime(integer);
    return {
      response_type: 'prime_under_100',
      response_value: valid ? String(integer) : raw,
      valid_response: valid,
      response_parse_error: valid ? '' : 'No prime number under 100 found',
    };
  }

  if (prompt.includes('number') || prompt.includes('basic_1_100') || prompt.includes('fair_draw') || prompt.includes('human_random')) {
    const valid = Number.isInteger(integer) && integer >= 1 && integer <= 100;
    return {
      response_type: 'integer_1_100',
      response_value: valid ? String(integer) : raw,
      valid_response: valid,
      response_parse_error: valid ? '' : 'No integer from 1 to 100 found',
    };
  }

  const valid = raw.length > 0 && raw.length <= 80 && /[A-Za-z]/.test(raw);
  return {
    response_type: 'free_text_choice',
    response_value: raw.toLowerCase(),
    valid_response: valid,
    response_parse_error: valid ? '' : 'No concise text choice found',
  };
}

return $input.all().map((item) => {
  const j = item.json || {};
  const usage = j.usage || j.data?.usage || j.body?.usage || {};
  const responseText = pickText([
    j.choices?.[0]?.message?.content,
    j.data?.choices?.[0]?.message?.content,
    j.body?.choices?.[0]?.message?.content,
    j.response?.choices?.[0]?.message?.content,
    j.output,
    j.response,
    j.text,
    j.message?.content,
  ]);

  const parsed = firstInteger(responseText);
  const valid = Number.isInteger(parsed) && parsed >= 1 && parsed <= 100;
  const responseParse = parseResponse(j.prompt_id, responseText);
  const promptTokens = maybeNumber(usage.prompt_tokens ?? usage.input_tokens);
  const completionTokens = maybeNumber(usage.completion_tokens ?? usage.output_tokens);
  const reasoningTokens = maybeNumber(usage.completion_tokens_details?.reasoning_tokens ?? usage.reasoning_tokens);
  const totalTokens = maybeNumber(usage.total_tokens) ?? (
    promptTokens !== null || completionTokens !== null
      ? Number(promptTokens || 0) + Number(completionTokens || 0)
      : null
  );
  const cost = maybeNumber(usage.cost ?? usage.total_cost ?? j.cost ?? j.total_cost);
  const latencyMs = Math.max(0, Date.now() - Number(j.requested_at_ms || Date.now()));
  const errorMessage = pickText([j.error?.message, j.data?.error?.message, j.body?.error?.message]);
  const errorStatus = pickText([j.error?.code, j.statusCode, j.status]);

  return {
    json: {
      run_id: j.run_id,
      sample_id: j.sample_id,
      measured_at: new Date().toISOString(),
      case_id: j.case_id,
      model_id: j.model_id,
      provider_label: j.provider_label,
      prompt_id: j.prompt_id,
      prompt_text: j.prompt_text,
      condition_label: j.condition_label,
      reasoning_effort: j.reasoning_effort,
      temperature: j.temperature,
      top_p: j.top_p,
      max_tokens: j.max_tokens,
      repetition_index: j.repetition_index,
      seed_policy: j.seed_policy,
      seed_value: j.seed_value,
      response_text: responseText,
      response_value: responseParse.response_value,
      response_type: responseParse.response_type,
      valid_response: responseParse.valid_response ? 'TRUE' : 'FALSE',
      response_parse_error: responseParse.response_parse_error,
      returned_model: j.model || '',
      provider_route: j.provider || '',
      finish_reason: j.choices?.[0]?.finish_reason || '',
      native_finish_reason: j.choices?.[0]?.native_finish_reason || '',
      reasoning_tokens: reasoningTokens ?? '',
      parsed_number: valid ? parsed : '',
      valid_number: valid ? 'TRUE' : 'FALSE',
      parse_error: valid ? '' : 'No integer from 1 to 100 found',
      is_odd: valid ? String(parsed % 2 !== 0).toUpperCase() : '',
      is_even: valid ? String(parsed % 2 === 0).toUpperCase() : '',
      is_prime: valid ? String(isPrime(parsed)).toUpperCase() : '',
      is_edge: valid ? String(parsed <= 10 || parsed >= 91).toUpperCase() : '',
      is_round: valid ? String(parsed % 10 === 0 || parsed % 5 === 0).toUpperCase() : '',
      contains_7: valid ? String(String(parsed).includes('7')).toUpperCase() : '',
      ends_with_7: valid ? String(String(parsed).endsWith('7')).toUpperCase() : '',
      distance_from_50: valid ? Math.abs(parsed - 50) : '',
      latency_ms: latencyMs,
      prompt_tokens: promptTokens ?? '',
      completion_tokens: completionTokens ?? '',
      total_tokens: totalTokens ?? '',
      cost_estimate_usd: cost ?? '',
      error_status: errorStatus,
      error_message: errorMessage,
      notes: j.notes || '',
      requested_provider_order: j.provider_order || '',
      requested_allow_fallbacks: j.allow_fallbacks || '',
      requested_require_parameters: j.require_parameters || '',
      requested_provider_ignore: j.provider_ignore || '',
    },
  };
});`;

const appendColumns = [
  'run_id',
  'sample_id',
  'measured_at',
  'case_id',
  'model_id',
  'provider_label',
  'prompt_id',
  'prompt_text',
  'condition_label',
  'temperature',
  'top_p',
  'max_tokens',
  'repetition_index',
  'seed_policy',
  'seed_value',
  'response_text',
  'parsed_number',
  'valid_number',
  'parse_error',
  'is_odd',
  'is_even',
  'is_prime',
  'is_edge',
  'is_round',
  'contains_7',
  'ends_with_7',
  'distance_from_50',
  'latency_ms',
  'prompt_tokens',
  'completion_tokens',
  'total_tokens',
  'cost_estimate_usd',
  'error_status',
  'error_message',
  'notes',
  'requested_provider_order',
  'requested_allow_fallbacks',
  'requested_require_parameters',
  'requested_provider_ignore',
  'reasoning_effort',
  'returned_model',
  'provider_route',
  'finish_reason',
  'native_finish_reason',
  'reasoning_tokens',
  'response_value',
  'response_type',
  'valid_response',
  'response_parse_error',
];

const mappingValue = Object.fromEntries(appendColumns.map((column) => [column, `={{ $json.${column} }}`]));

const workflow = {
  name: 'Random Number Fingerprint - Experiment Runner (Template)',
  nodes: [
    {
      parameters: {},
      id: 'b3eaf47a-9c7d-4d79-a85a-4a2cdb58a101',
      name: 'Manual Trigger',
      type: 'n8n-nodes-base.manualTrigger',
      typeVersion: 1,
      position: [-1220, 80],
    },
    {
      parameters: {
        operation: 'read',
        documentId: { __rl: true, mode: 'id', value: sheetIdPlaceholder },
        sheetName: { __rl: true, mode: 'name', value: 'ExperimentCases' },
        options: {},
      },
      id: '7440e82e-2ffd-4ffd-b3f7-1f6e85e4dd76',
      name: 'Read Experiment Cases',
      type: 'n8n-nodes-base.googleSheets',
      typeVersion: 4.7,
      position: [-1000, 80],
      credentials: null,
    },
    {
      parameters: { jsCode: expandCode },
      id: 'e63835a6-0474-47ad-a8ec-f53083e03cc8',
      name: 'Expand Experiment Matrix',
      type: 'n8n-nodes-base.code',
      typeVersion: 2,
      position: [-760, 80],
    },
    {
      parameters: {
        method: 'POST',
        url: 'https://openrouter.ai/api/v1/chat/completions',
        authentication: 'predefinedCredentialType',
        nodeCredentialType: 'openRouterApi',
        sendBody: true,
        specifyBody: 'json',
        jsonBody: "={{ JSON.stringify((() => { const splitList = (value) => String(value || '').split(',').map((v) => v.trim()).filter(Boolean); const body = { model: $json.model_id || 'openai/gpt-chat-latest', messages: [{ role: 'user', content: $json.prompt_text || 'Pick a random integer from 1 to 100. Reply with only the number.' }], temperature: Number($json.temperature || 1), top_p: Number($json.top_p || 1), max_tokens: Math.max(16, Number($json.max_tokens || 16)), stream: false }; const providerOrder = splitList($json.provider_order); const providerIgnore = splitList($json.provider_ignore); if (providerOrder.length || providerIgnore.length || $json.allow_fallbacks || $json.require_parameters) { body.provider = {}; if (providerOrder.length) body.provider.order = providerOrder; if (providerIgnore.length) body.provider.ignore = providerIgnore; if ($json.allow_fallbacks !== '' && $json.allow_fallbacks !== undefined && $json.allow_fallbacks !== null) body.provider.allow_fallbacks = String($json.allow_fallbacks).toLowerCase() !== 'false'; if (String($json.require_parameters || '').toLowerCase() === 'true') body.provider.require_parameters = true; } if ($json.reasoning_effort) body.reasoning = { effort: $json.reasoning_effort, exclude: true }; if ($json.seed_value !== '' && $json.seed_value !== undefined && $json.seed_value !== null) body.seed = Number($json.seed_value); return body; })()) }}",
        options: {
          response: {
            response: {
              neverError: true,
              responseFormat: 'json',
            },
          },
        },
      },
      id: 'ad9bcfcb-d394-4222-a608-7f3b77108f1b',
      name: 'OpenRouter Chat Completion',
      type: 'n8n-nodes-base.httpRequest',
      typeVersion: 4.2,
      position: [-500, -120],
      credentials: null,
    },
    {
      parameters: {
        mode: 'combine',
        combineBy: 'combineByPosition',
        options: {},
      },
      id: 'd90dcf29-4d03-463a-b553-e4ad4164fae5',
      name: 'Merge Request + Response',
      type: 'n8n-nodes-base.merge',
      typeVersion: 3.2,
      position: [-260, 80],
    },
    {
      parameters: { jsCode: parseCode },
      id: '711c71ee-4a9b-4a94-aebf-f2814ed9cf02',
      name: 'Parse Random Number Result',
      type: 'n8n-nodes-base.code',
      typeVersion: 2,
      position: [0, 80],
    },
    {
      parameters: {
        operation: 'append',
        documentId: { __rl: true, mode: 'id', value: sheetIdPlaceholder },
        sheetName: { __rl: true, mode: 'name', value: 'ExperimentResults' },
        columns: {
          mappingMode: 'defineBelow',
          value: mappingValue,
          schema: [],
          attemptToConvertTypes: false,
          convertFieldsToString: false,
        },
        options: {},
      },
      id: '600553e5-7862-4934-b9b6-d67c710d0413',
      name: 'Append Experiment Results',
      type: 'n8n-nodes-base.googleSheets',
      typeVersion: 4.7,
      position: [260, 80],
      credentials: null,
    },
  ],
  connections: {
    'Manual Trigger': {
      main: [[{ node: 'Read Experiment Cases', type: 'main', index: 0 }]],
    },
    'Read Experiment Cases': {
      main: [[{ node: 'Expand Experiment Matrix', type: 'main', index: 0 }]],
    },
    'Expand Experiment Matrix': {
      main: [[
        { node: 'OpenRouter Chat Completion', type: 'main', index: 0 },
        { node: 'Merge Request + Response', type: 'main', index: 0 },
      ]],
    },
    'OpenRouter Chat Completion': {
      main: [[{ node: 'Merge Request + Response', type: 'main', index: 1 }]],
    },
    'Merge Request + Response': {
      main: [[{ node: 'Parse Random Number Result', type: 'main', index: 0 }]],
    },
    'Parse Random Number Result': {
      main: [[{ node: 'Append Experiment Results', type: 'main', index: 0 }]],
    },
  },
  pinData: {},
  settings: { executionOrder: 'v1' },
  staticData: null,
  tags: [],
  triggerCount: 0,
  updatedAt: '2026-05-21T00:00:00.000Z',
  versionId: null,
  active: false,
  meta: { templateCredsSetupCompleted: false },
};

mkdirSync(dirname(outputPath), { recursive: true });
writeFileSync(outputPath, JSON.stringify(workflow, null, 2) + '\n');
console.log(`Wrote ${outputPath}`);

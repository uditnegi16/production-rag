import http from 'k6/http';
import { check, sleep } from 'k6';
import { Rate, Trend } from 'k6/metrics';

const errorRate = new Rate('error_rate');
const fallbackRate = new Rate('fallback_rate');
const latencyTrend = new Trend('query_latency_ms');

export const options = {
  stages: [
    { duration: '20s', target: 5  },
    { duration: '40s', target: 30 },
    { duration: '20s', target: 0  },
  ],
  thresholds: {
    http_req_duration: ['p(95)<30000'],
    error_rate: ['rate<0.3'],
    fallback_rate: ['rate<0.2'],
  },
};

const QUERIES = [
  'What is a large language model?',
  'What is pretraining?',
  'What is fine tuning?',
  'What is a token?',
  'What is the transformer architecture?',
  'What is an embedding?',
  'What is the context window of a language model?',
  'What is a foundation model?',
];

export default function () {
  const query = QUERIES[Math.floor(Math.random() * QUERIES.length)];

  const res = http.post(
    'http://localhost:8000/api/v1/query',
    JSON.stringify({ query: query, top_k: 10, top_n: 5 }),
    { headers: { 'Content-Type': 'application/json' } }
  );

  check(res, {
    'status is 200': (r) => r.status === 200,
    'has answer': (r) => JSON.parse(r.body).answer !== null,
    'not fallback': (r) => JSON.parse(r.body).is_fallback === false,
  });

  errorRate.add(res.status !== 200);

  if (res.status === 200) {
    const body = JSON.parse(res.body);
    fallbackRate.add(body.is_fallback === true);
    latencyTrend.add(body.latency_ms);
  }

  sleep(2);
}
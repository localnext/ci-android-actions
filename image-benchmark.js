import http from 'k6/http';
import { check, sleep } from 'k6';
import { Trend } from 'k6/metrics';

const ttfb = new Trend('ttfb');
const contentSize = new Trend('content_size');

export const options = {
  scenarios: {
    test_vercel_direct: {
      exec: 'testVercel',
      executor: 'constant-vus',
      vus: 5, 
      duration: '2m',
    },
    test_custom_domain: {
      exec: 'testCustom',
      executor: 'constant-vus',
      vus: 5,
      duration: '2m',
      startTime: '2m10s', // Run AFTER the first test finishes to isolate results
    },
  },
  thresholds: {
    http_req_failed: ['rate<0.05'], // Allow <5% failure (flaky networks)
    ttfb: ['p(95)<1500'], // 95% of requests should start within 1.5s
  },
};

// Common headers to look like a real Chrome browser on macOS
const headers = {
  'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
  'Accept': 'image/avif,image/webp,image/apng,image/svg+xml,image/*,*/*;q=0.8',
  'Accept-Encoding': 'gzip, deflate, br',
  'Connection': 'keep-alive',
};

export function testVercel() {
  const url = 'https://github-readme-stats-nu-six-29.vercel.app/api?username=shiinasaku';
  runTest(url, 'Vercel Direct');
}

export function testCustom() {
  const url = 'https://card.shiina.xyz/card/shiinasaku';
  runTest(url, 'Custom Domain');
}

function runTest(url, tag) {
  const res = http.get(url, { headers: headers, tags: { endpoint: tag } });

  ttfb.add(res.timings.waiting);
  contentSize.add(res.body.length);

  check(res, {
    'status is 200': (r) => r.status === 200,
    // CRITICAL: Ensure we actually got an SVG, not a text error
    'is svg image': (r) => r.headers['Content-Type'] && r.headers['Content-Type'].includes('svg'),
    // Ensure the image isn't empty or a tiny error stub
    'body size > 1kb': (r) => r.body.length > 1000, 
  });

  // Random sleep 1-3s to simulate organic traffic and avoid Vercel "Bot Detection"
  sleep(Math.random() * 2 + 1);
      }
    

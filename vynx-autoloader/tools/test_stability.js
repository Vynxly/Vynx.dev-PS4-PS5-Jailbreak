const assert = require('node:assert/strict');
const fs = require('node:fs');
const path = require('node:path');
const vm = require('node:vm');
const { spawnSync } = require('node:child_process');

const frontend = path.join(__dirname, '../frontend/vynx/ps5-autoload');
const poops = fs.readFileSync(path.join(frontend, 'slopkit/slopkit/poops.js'), 'utf8');
const cleanupSource = poops.slice(
  poops.indexOf('  async function cleanup(opts) {'),
  poops.indexOf('  let cleanupRun = null,'),
);
assert.ok(cleanupSource.startsWith('  async function cleanup(opts) {'));
assert.ok(cleanupSource.includes('return rep;'));

async function cleanupCase(aliasesRepaired, failure, jailbroken = true) {
  const calls = [];
  const marks = [];
  const groups = ['iov', 'uioRead', 'uioWrite'].map((name) => ({
    name, spawned: [{ jbWid: 0 }],
    S: { get: () => failure === name ? 1 : 3 },
  }));
  const S = {
    kernelWrites: jailbroken ? 1 : 0, jailbroken: true, aliasesRepaired,
    iovGroup: groups[0], uioReadGroup: groups[1], uioWriteGroup: groups[2],
    doNotClose: new Set(), groupsStillLive: [],
  };
  const state = { fdOpen: new Set([10, 11, 12]), cleanupFailed: '' };
  const sandbox = {
    S, state, TK: { ST_EXITED: 3 },
    untrack: (fd) => state.fdOpen.delete(fd),
    flushMark: (...args) => marks.push(args),
    unblockGroup: async (g) => { calls.push('unblock:' + g.name); return { rounds: 1 }; },
    forceSettled: (g) => calls.push('settle:' + g.name),
    H: { terminate: async (g) => {
      calls.push('terminate:' + g.name);
      if (failure === 'throw:' + g.name) throw new Error('termination failed');
      return { exitedMs: failure === 'timeout:' + g.name ? -1 : 5 };
    } },
  };
  vm.createContext(sandbox);
  vm.runInContext(cleanupSource + '\nglobalThis.cleanupUnderTest = cleanup;', sandbox);
  const report = await sandbox.cleanupUnderTest();
  assert.deepEqual([...S.doNotClose], [10, 11, 12]);
  assert.equal(state.fdOpen.size, 0);
  assert.equal(report.teardown, null);
  assert.equal(report.pipesClosed, 0);
  assert.ok(state.cleanupFailed.includes('reboot required'));
  return { S, report, calls, marks };
}

async function relapseChecks() {
  const source = fs.readFileSync(path.join(frontend, 'relapse/src/relapse_exploit.js'), 'utf8');
  const delays = [];
  const sandbox = {
    window: { KRW: {
      oid: { a: { kindByte3: 1 }, b: { kindByte3: 2 }, originalKind: 3 },
      proc: { aioInfo: 0 }, aio: { group: { num: 0, state: 4, waiters: 8 } },
    } },
    int64: function () {},
    setTimeout: (resolve, ms) => { delays.push(ms); resolve(); },
    SYS_PIPE2: 1,
  };
  vm.createContext(sandbox);
  vm.runInContext(source.replace(/^import .*;\r?\n/, '')
    .replace('export async function', 'async function')
    + '\nglobalThis.KernelExploitUnderTest = KernelExploit;', sandbox);
  const engine = new sandbox.KernelExploitUnderTest({ malloc: () => ({}) }, {}, () => {});
  Object.assign(engine, {
    nameToMib: async () => [1], oidKind: async () => 3,
    raiseFdLimit: async () => {}, parkAioWorkers: async () => {},
    makeOidWritable: async () => true, steerOidWindow: async () => true,
    testKernelRead: async () => true, testKernelWrite: async () => true,
    prepareHighWriter: async () => true,
  });
  assert.equal(await engine.armKernelReadWrite(), true);
  assert.deepEqual(delays, [1000]);

  const pointer = { add32: () => pointer };
  Object.assign(engine, {
    curproc: pointer, armedGroups: [[1, 2]],
    kread64: async () => ({ value: pointer }), isKernelPointer: () => true,
    lookupAioGroup: async () => null,
  });
  assert.equal(await engine.defuseAioGroups(), false);
  assert.deepEqual(delays, [1000, 100, 100]);

  let flags;
  Object.assign(engine, {
    readKernelPointer: async () => pointer, alloc: () => ({}), clear: () => {},
    sysInt: async (_number, _pair, mode) => { flags = mode; return -1; },
  });
  assert.equal(await engine.locatePipes(), false);
  assert.equal(flags, 4);
}

function offsetChecks() {
  for (const [firmware, sleep, cpu] of [
    ['9.05', 0x27560, 0x11e0], ['11.40', 0x27890, 0x11f0],
    ['11.60', 0x27890, 0x11f0],
  ]) {
    const source = fs.readFileSync(path.join(frontend, 'slopkit/offsets', firmware + '.js'), 'utf8');
    const context = vm.createContext({ window: {} });
    vm.runInContext(source, context);
    assert.equal(vm.runInContext('OFFSET_lk_sleep', context), sleep);
    assert.equal(vm.runInContext('OFFSET_lk_sceKernelGetCurrentCpu', context), cpu);
  }
}

async function handoffChecks() {
  const html = fs.readFileSync(path.join(frontend, 'slopkit/slopkit/poops.html'), 'utf8');
  const decision = html.slice(html.indexOf('    const payloadSuccess ='),
    html.indexOf('    const fullSuccess ='));
  const tail = html.slice(html.lastIndexOf('    if (payloadSuccess) {'),
    html.indexOf('\nlet bootChainReady = false;')).trim();
  // The last brace belongs to runLadder, not the handoff branch.
  const branch = tail.slice(0, tail.lastIndexOf('}'));
  for (const [repaired, live, dead, expected] of [
    [true, [], false, true], [false, [], false, false],
    [true, ['uioRead'], false, false], [true, [], true, false],
  ]) {
    let sent = 0;
    const messages = [];
    const context = vm.createContext({
      cfg: { payload: '1', autoload: 'payload.elf' }, elfldrSpawned: true,
      chainDead: dead, engine: { S: { aliasesRepaired: repaired, groupsStillLive: live } },
      flushMark: () => {}, payloadMenuEl: { classList: { contains: () => true } },
      startAutoload: () => sent++, showPayloadMenu: () => {},
      window: { parent: { postMessage: (message) => messages.push(message) } },
    });
    vm.runInContext(decision + branch, context);
    assert.equal(sent, expected ? 1 : 0);
    if (!expected) assert.equal(messages[0].ok, false);
  }
  for (const script of html.matchAll(/<script\b([^>]*)>([\s\S]*?)<\/script>/g)) {
    if (/\bsrc=/.test(script[1])) continue;
    const parsed = spawnSync(process.execPath, ['--check', '--input-type=module'],
      { input: script[2], encoding: 'utf8' });
    assert.equal(parsed.status, 0, parsed.stderr);
  }
  const existingLoaderCheck = html.slice(
    html.indexOf('    // Already jailbroken this boot?'),
    html.lastIndexOf('    renderNav("", false);'),
  );
  const messages = [];
  const context = vm.createContext({
    cfg: { autoload: 'payload.elf' }, stage: () => {}, screenLine: () => {},
    bootChain: async () => {}, refreshConsoleNetworkInfo: async () => {},
    probeExistingElfLoader: async () => true, sendRemoteEvents: () => {},
    startAutoload: () => assert.fail('existing loader must not receive bootstrap again'),
    window: { parent: { postMessage: (message) => messages.push(message) } },
  });
  await vm.runInContext('(async function () {' + existingLoaderCheck + '})()', context);
  assert.equal(messages[0].ok, false);
  assert.equal(messages[0].why, 'Already jailbroken.');
}

(async () => {
  const parked = await cleanupCase(false);
  assert.deepEqual(parked.calls, []);
  assert.deepEqual([...parked.S.groupsStillLive], ['iov', 'uioRead', 'uioWrite']);
  const success = await cleanupCase(true);
  assert.deepEqual(success.calls, [
    'unblock:iov', 'settle:iov', 'terminate:iov',
    'unblock:uioRead', 'settle:uioRead', 'terminate:uioRead',
    'unblock:uioWrite', 'settle:uioWrite', 'terminate:uioWrite',
  ]);
  assert.deepEqual([...success.report.groupsLive], []);
  for (const failure of ['uioRead', 'throw:uioRead', 'timeout:uioRead']) {
    const result = await cleanupCase(true, failure);
    assert.deepEqual([...result.S.groupsStillLive], ['uioRead']);
    assert.deepEqual([...result.report.groupsLive], ['uioRead']);
    assert.ok(result.calls.includes('terminate:uioWrite'));
  }
  assert.deepEqual([...(await cleanupCase(true, null, false)).S.groupsStillLive], []);
  await relapseChecks();
  offsetChecks();
  await handoffChecks();
  console.log('OK: KP repair gate, racer failures, descriptor hold, payload handoff, Relapse delays/pipes, and Poops offsets');
})().catch((error) => { console.error(error); process.exitCode = 1; });

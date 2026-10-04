const $ = s => document.querySelector(s);
let state = {};
let queue = [];

async function send(type, payload) {
  return chrome.runtime.sendMessage(Object.assign({ type: type }, payload || {}));
}

async function refresh() {
  const res = await send('GET_STATE');
  state = res.state || {};
  queue = res.queue || [];
  $('#batch').value = state.batch || 'A';
  const current = queue.find(x => x.id === state.currentId);
  const vals = Object.values(state.items || {});
  const done = vals.filter(x => x.status === 'downloaded').length;
  const failed = vals.filter(x => x.status === 'failed').length;
  $('#headline').textContent = state.running ? '正在自动处理' : '已停止 / 等待开始';
  $('#detail').textContent = current ? current.id + ' · ' + current.title : '完成 ' + done + ' · 失败 ' + failed + ' · 无当前任务';
  $('#queue').innerHTML = queue
    .filter(x => (state.batch || 'A') === 'all' || x.batch === (state.batch || 'A'))
    .map(x => {
      const s = (state.items && state.items[x.id] && state.items[x.id].status) || 'todo';
      const cls = x.id === state.currentId ? 'current' : (s === 'downloaded' ? 'done' : (s === 'failed' ? 'failed' : ''));
      return '<li class="' + cls + '">' + x.id + ' · ' + x.title + '<small>' + s + ' · ' + (x.doi || x.alternate_url || '') + '</small></li>';
    }).join('');
}

$('#start').onclick = async () => { await send('START', { batch: $('#batch').value }); refresh(); };
$('#open').onclick = async () => { await send('OPEN_NEXT', { batch: $('#batch').value }); refresh(); };
$('#stop').onclick = async () => { await send('STOP'); refresh(); };
$('#retry').onclick = async () => { await send('RETRY'); refresh(); };
$('#skip').onclick = async () => { await send('SKIP'); refresh(); };
$('#refresh').onclick = async () => { await send('REFRESH_QUEUE'); refresh(); };
$('#batch').onchange = async () => { await send('SET_BATCH', { batch: $('#batch').value }); refresh(); };

refresh();
setInterval(refresh, 1500);

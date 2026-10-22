/* 구월경희한의원 원내 태블릿 모드 (주소에 ?kiosk=1 이 있을 때만 작동)
 * - 작성 내용을 기기에 남기지 않음 (이어서 하기 없음)
 * - 2분 30초 동안 손대지 않으면 확인 창 → 30초 뒤 처음 화면(/tablet/)으로
 * - 제출 후: 고른 문진이 더 있으면 다음 문진으로, 없으면 완료 화면 → 처음 화면
 * - 성명·생년월일 등은 같은 환자의 다음 문진으로 이어받음, 직원이 넣은 차트번호를 함께 전송
 */
(function () {
  var qs = new URLSearchParams(location.search);
  var K = { on: qs.get('kiosk') === '1' };
  window.GKH_KIOSK = K;
  if (!K.on) return;

  var ss = window.sessionStorage;
  function get(k) { try { return JSON.parse(ss.getItem(k) || 'null'); } catch (e) { return null; } }
  function set(k, v) { try { ss.setItem(k, JSON.stringify(v)); } catch (e) {} }
  var IDLE = 150, GRACE = 30;

  K.patient = function () { return get('gkh_k_patient') || {}; };
  K.setPatient = function (p) { var o = K.patient(); for (var k in p) if (p[k] != null && p[k] !== '') o[k] = p[k]; set('gkh_k_patient', o); };
  K.cfg = function () { return get('gkh_k_cfg') || {}; };
  K.chart = function () { return K.cfg().chart || ''; };
  K.home = function () { try { ss.clear(); localStorage.removeItem('gkh_intake_v1'); } catch (e) {} location.replace('/tablet/'); };
  K.nextUrl = function () {
    var q = K.cfg().queue || [], cur = location.pathname.split('/').filter(Boolean)[0], i = q.indexOf(cur);
    return (i >= 0 && q[i + 1]) ? '/' + q[i + 1] + '/?kiosk=1' : null;
  };
  K.progress = function () {
    var q = K.cfg().queue || [], cur = location.pathname.split('/').filter(Boolean)[0], i = q.indexOf(cur);
    return q.length > 1 && i >= 0 ? (i + 1) + ' / ' + q.length : '';
  };

  var css = document.createElement('style');
  css.textContent =
    '.kz-ov{position:fixed;inset:0;background:rgba(20,28,25,.55);z-index:50;display:flex;align-items:center;justify-content:center;padding:1.2rem}' +
    '.kz-box{background:#fff;border-radius:1.2rem;padding:1.6rem 1.4rem;max-width:30rem;width:100%;text-align:center;font-family:inherit}' +
    '.kz-box h2{font-size:1.4rem;margin-bottom:.5rem}.kz-box p{color:#5b6662;margin-bottom:1.1rem;line-height:1.5}' +
    '.kz-box button{width:100%;min-height:3.4rem;border:none;border-radius:.9rem;background:#2f6b57;color:#fff;font:inherit;font-weight:800;font-size:1.1rem;margin-top:.5rem}' +
    '.kz-box button.sec{background:#fff;border:1.5px solid #d6ddda;color:#5b6662}' +
    '.kz-badge{position:fixed;right:.6rem;bottom:5.6rem;z-index:8;background:#2f6b57;color:#fff;font-size:.75rem;font-weight:700;padding:.25rem .6rem;border-radius:1rem;opacity:.85}' +
    '.kz-home{border:1.5px solid #d6ddda;border-radius:.6rem;padding:.25rem .55rem;font-size:.75rem;font-weight:700;color:#8b9692;background:#fff;margin-left:.4rem}';
  document.head.appendChild(css);

  var timer, warnEl = null, cd;
  function arm() { clearTimeout(timer); timer = setTimeout(warn, IDLE * 1000); }
  function warn() {
    var left = GRACE;
    warnEl = document.createElement('div'); warnEl.className = 'kz-ov';
    warnEl.innerHTML = '<div class="kz-box"><h2>계속 작성하시겠어요?</h2><p>한동안 입력이 없어 <b id="kz-s">' + left + '</b>초 뒤 처음 화면으로 돌아갑니다.<br>작성하던 내용은 지워집니다.</p><button id="kz-go">계속 작성하기</button></div>';
    document.body.appendChild(warnEl);
    document.getElementById('kz-go').onclick = function () { clearInterval(cd); warnEl.remove(); warnEl = null; arm(); };
    cd = setInterval(function () { left--; var s = document.getElementById('kz-s'); if (s) s.textContent = left; if (left <= 0) { clearInterval(cd); K.home(); } }, 1000);
  }
  ['click', 'touchstart', 'input', 'keydown', 'scroll'].forEach(function (ev) {
    document.addEventListener(ev, function () { if (!warnEl) arm(); }, { passive: true, capture: true });
  });

  K.done = function (el) {
    clearTimeout(timer);
    var nx = K.nextUrl(), sec = nx ? 4 : 10;
    el.innerHTML = nx
      ? '<div class="done"><div class="ok">✓</div><h2>제출되었습니다</h2><p>잠시 후 다음 문진표로 넘어갑니다.</p><div class="kz-box" style="margin:1.4rem auto 0;padding:0;background:none"><button id="kz-next">다음 문진표 작성하기</button></div></div>'
      : '<div class="done"><div class="ok">✓</div><h2>모두 작성하셨습니다</h2><p>감사합니다.<br><b>태블릿을 데스크에 돌려주세요.</b></p><div class="kz-box" style="margin:1.4rem auto 0;padding:0;background:none"><button id="kz-end" class="sec">처음 화면으로</button></div></div>';
    var go = function () { if (nx) location.replace(nx); else K.home(); };
    var b = document.getElementById('kz-next') || document.getElementById('kz-end'); if (b) b.onclick = go;
    setTimeout(go, sec * 1000);
  };

  document.addEventListener('DOMContentLoaded', function () {
    document.body.classList.add('big');
    var fb = document.getElementById('fontBtn'); if (fb) fb.setAttribute('aria-pressed', 'true');
    var p = K.progress();
    if (p) { var bd = document.createElement('div'); bd.className = 'kz-badge'; bd.textContent = '문진표 ' + p; document.body.appendChild(bd); }
    var bar = document.querySelector('.top .bar .right') || document.querySelector('.top .bar');
    if (bar) { var h = document.createElement('button'); h.className = 'kz-home'; h.textContent = '처음으로'; h.onclick = function () { if (confirmHome()) K.home(); }; bar.appendChild(h); }
    arm();
  });
  function confirmHome() {
    var ov = document.createElement('div'); ov.className = 'kz-ov';
    ov.innerHTML = '<div class="kz-box"><h2>처음 화면으로 갈까요?</h2><p>작성하던 내용은 지워집니다.</p><button id="kz-y">처음 화면으로</button><button id="kz-n" class="sec">계속 작성하기</button></div>';
    document.body.appendChild(ov);
    document.getElementById('kz-y').onclick = function () { K.home(); };
    document.getElementById('kz-n').onclick = function () { ov.remove(); };
    return false;
  }
})();

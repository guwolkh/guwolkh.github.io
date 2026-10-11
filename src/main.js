// 'N년째' 문구: 사이트를 다시 올리지 않아도 방문자가 보는 해에 맞춰 계산
(function () {
  var start = parseInt(document.body.getAttribute('data-career-start'), 10);
  if (!start) return;
  var years = String(new Date().getFullYear() - start + 1);
  document.querySelectorAll('[data-career-years]').forEach(function (el) {
    el.textContent = years;
  });
})();

// 예약 선택 창 열기/닫기
(function () {
  var sheet = document.getElementById('booking-sheet');
  if (!sheet) return;
  var lastFocus = null;

  function open() {
    lastFocus = document.activeElement;
    sheet.hidden = false;
    document.body.style.overflow = 'hidden';
    var first = sheet.querySelector('.sheet-option, .sheet-close');
    if (first) first.focus();
  }
  function close() {
    sheet.hidden = true;
    document.body.style.overflow = '';
    if (lastFocus) lastFocus.focus();
  }

  document.querySelectorAll('[data-open-booking]').forEach(function (el) {
    el.addEventListener('click', open);
  });
  document.querySelectorAll('[data-close-booking]').forEach(function (el) {
    el.addEventListener('click', close);
  });
  document.addEventListener('keydown', function (e) {
    if (e.key === 'Escape' && !sheet.hidden) close();
  });
})();

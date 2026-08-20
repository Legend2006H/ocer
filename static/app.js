const form = document.querySelector('#extract-form');
const fileInput = document.querySelector('#pdf');
const status = document.querySelector('#status');
const results = document.querySelector('#results');
const output = document.querySelector('#output');
let extractedText = '';

form.addEventListener('submit', async (event) => {
  event.preventDefault();
  if (!fileInput.files[0]) return;
  status.textContent = 'Reading your PDF…'; results.hidden = true;
  const data = new FormData();
  data.append('pdf', fileInput.files[0]);
  data.append('ocr', document.querySelector('#ocr').checked ? 'true' : 'false');
  data.append('language', document.querySelector('#language').value);
  try {
    const response = await fetch('/extract', {method: 'POST', body: data});
    const result = await response.json();
    if (!response.ok) throw new Error(result.error || 'Extraction failed.');
    extractedText = result.text; output.value = result.text;
    document.querySelector('#summary').textContent = `${result.pages.length} page${result.pages.length === 1 ? '' : 's'} processed`;
    document.querySelector('#pages').innerHTML = result.pages.map(p => `<article><b>Page ${p.page}</b><span>${p.source}</span><small>${p.characters.toLocaleString()} characters</small></article>`).join('');
    status.textContent = result.warnings.join(' ') || 'Done.'; results.hidden = false;
  } catch (error) { status.textContent = error.message; }
});
document.querySelector('#download').addEventListener('click', () => {
  const link = Object.assign(document.createElement('a'), {href: URL.createObjectURL(new Blob([extractedText], {type: 'text/plain'})), download: 'extracted-text.txt'});
  link.click(); URL.revokeObjectURL(link.href);
});

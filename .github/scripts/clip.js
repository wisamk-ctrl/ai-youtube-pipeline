// Cut an issue or comment body to GitHub's limit (65,536 chars) without leaving a <details> block
// or a ``` fence open — an unclosed one swallows the rest of the page, or hides the cut entirely.
//   const clip = require(`${process.env.GITHUB_WORKSPACE}/.github/scripts/clip.js`);
//   body: clip(text)            // default 64,000
module.exports = function clip(body, max = 64000) {
  body = String(body ?? '');
  if (body.length <= max) return body;
  const note = "\n\n_… cut to fit GitHub's limit; the full text is in the week's artifact._";
  let s = body.slice(0, Math.max(0, max - 400));        // room for the closers and the note
  const nl = s.lastIndexOf('\n');
  if (nl > s.length / 2) s = s.slice(0, nl);           // never end mid-line (or mid-tag)
  let tail = '';
  if (((s.match(/^[ \t]*```/gm) || []).length) % 2) tail += '\n```';
  const opened = (s.match(/<details\b/gi) || []).length;
  const closed = (s.match(/<\/details>/gi) || []).length;
  for (let i = closed; i < opened; i++) tail += '\n</details>';
  return s + tail + note;
};

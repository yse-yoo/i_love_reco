const questions = [
  // === 外向・内向（E/I） ===
  { q: "初対面でも積極的に話しかけることができる", axis: "EI", positive: "E" },
  { q: "大勢の場にいると元気が出る", axis: "EI", positive: "E" },
  { q: "話すことで考えがまとまる", axis: "EI", positive: "E" },
  { q: "知らない人ともすぐに会話できる", axis: "EI", positive: "E" },
  { q: "注目されることに抵抗がない", axis: "EI", positive: "E" },
  { q: "一人の時間がないと疲れる", axis: "EI", positive: "I" },
  { q: "静かな環境で力を発揮する", axis: "EI", positive: "I" },
  { q: "人前で話すのはあまり得意ではない", axis: "EI", positive: "I" },
  { q: "一人で過ごすのが好き", axis: "EI", positive: "I" },
  { q: "深い関係の少人数を大事にする", axis: "EI", positive: "I" },

  // === 現実・直感（S/N） ===
  { q: "現実的な選択をする", axis: "SN", positive: "S" },
  { q: "五感で感じたことを重視する", axis: "SN", positive: "S" },
  { q: "経験に基づいて考える", axis: "SN", positive: "S" },
  { q: "具体的な説明の方が安心する", axis: "SN", positive: "S" },
  { q: "事実や数字を大事にする", axis: "SN", positive: "S" },
  { q: "ひらめきを信じる", axis: "SN", positive: "N" },
  { q: "抽象的なアイデアに惹かれる", axis: "SN", positive: "N" },
  { q: "未来の可能性にワクワクする", axis: "SN", positive: "N" },
  { q: "比喩表現をよく使う", axis: "SN", positive: "N" },
  { q: "直感で物事を判断することが多い", axis: "SN", positive: "N" },

  // === 思考・感情（T/F） ===
  { q: "論理的に考えるのが得意", axis: "TF", positive: "T" },
  { q: "正しさを重視する", axis: "TF", positive: "T" },
  { q: "感情より理屈を優先する", axis: "TF", positive: "T" },
  { q: "議論で勝つことに喜びを感じる", axis: "TF", positive: "T" },
  { q: "物事を冷静に分析する", axis: "TF", positive: "T" },
  { q: "人の気持ちに共感しやすい", axis: "TF", positive: "F" },
  { q: "相手の立場を考える", axis: "TF", positive: "F" },
  { q: "思いやりを大事にする", axis: "TF", positive: "F" },
  { q: "感情の変化に敏感", axis: "TF", positive: "F" },
  { q: "優しさを大切にしている", axis: "TF", positive: "F" },

  // === 判断・柔軟（J/P） ===
  { q: "計画的に物事を進めたい", axis: "JP", positive: "J" },
  { q: "スケジュール管理が得意", axis: "JP", positive: "J" },
  { q: "予定通りにいかないと不安", axis: "JP", positive: "J" },
  { q: "締切は守るタイプ", axis: "JP", positive: "J" },
  { q: "順序立てて行動するのが好き", axis: "JP", positive: "J" },
  { q: "思いつきで動くことが多い", axis: "JP", positive: "P" },
  { q: "その場の流れに身を任せる", axis: "JP", positive: "P" },
  { q: "予定は立てず臨機応変に対応する", axis: "JP", positive: "P" },
  { q: "気分で物事を決める", axis: "JP", positive: "P" },
  { q: "締切直前に集中するタイプ", axis: "JP", positive: "P" }
];
const typeImages = {
  INFP: "/static/images/INFP.png",
  INFJ: "/static/images/INFJ.png",
  INTJ: "/static/images/INTJ.png",
  INTP: "/static/images/INTP.png",
  ISFP: "/static/images/ISFP.png",
  ISFJ: "/static/images/ISFJ.png",
  ISTJ: "/static/images/ISTJ.png",
  ISTP: "/static/images/ISTP.png",
  ENFP: "/static/images/ENFP.png",
  ENFJ: "/static/images/ENFJ.png",
  ENTJ: "/static/images/ENTJ.png",
  ENTP: "/static/images/ENTP.png",
  ESFP: "/static/images/ESFP.png",
  ESFJ: "/static/images/ESFJ.png",
  ESTP: "/static/images/ESTP.png",
  ESTJ: "/static/images/ESTJ.png"
};


let current = 0;
const score = { EI: 0, SN: 0, TF: 0, JP: 0 };

function showQuestion() {
  const qBox = document.getElementById("question-box");
  qBox.classList.remove("fade-in");
  void qBox.offsetWidth; // trigger reflow
  qBox.classList.add("fade-in");

  const q = questions[current];
  document.getElementById("question").textContent = q.q;
  document.getElementById("question-count").textContent = `${current + 1} / ${questions.length} 問`;
  document.getElementById("slider").value = 0;
  document.getElementById("progress-bar").style.width = `${(current / questions.length) * 103}%`;
}

function submitAnswer() {
  const value = parseInt(document.getElementById("slider").value);
  const { axis, positive } = questions[current];
  score[axis] += (positive === getPositive(axis)) ? value : -value;

  current++;
  if (current < questions.length) {
    showQuestion();
  } else {
    showResult();
  }
}

function getPositive(axis) {
  const map = { EI: "E", SN: "S", TF: "T", JP: "J" };
  return map[axis];
}

function getResultType() {
  return [
    score.EI >= 0 ? "E" : "I",
    score.SN >= 0 ? "S" : "N",
    score.TF >= 0 ? "T" : "F",
    score.JP >= 0 ? "J" : "P"
  ].join("");
}

function showResult() {
  document.getElementById("question-box").style.display = "none";
  document.getElementById("result-box").style.display = "block";

  const type = getResultType();
  document.getElementById("result-type").textContent = `あなたのタイプは：${type}`;
  document.getElementById("result-desc").textContent = getTypeDescription(type);

  const match = typeMatches[type];
  const matchText = match.match.map(m =>
    `<span class="match-type" onclick="showMatchDetail('${m}')">${m}</span>`
  ).join("・");

  document.getElementById("result-match").innerHTML =
    `相性が良いタイプ：${matchText}（${match.reason}）`;

  document.getElementById("match-details").style.display = "none";
}




function getTypeDescription(type) {
  const descriptions = {
    INFP: "仲介者 / Mediator：理想を追い求める仲介者。感受性が強く、他人の痛みに敏感です。",
    INFJ: "提唱者 / Advocate：内省的で直感的、人の成長を助けるカウンセラータイプ。",
    INTJ: "建築家 / Architect：戦略家で分析的。目標に向かって冷静に進むタイプ。",
    INTP: "論理学者 / Logician：理論と知識を探求する建築家タイプ。",
    ISFP: "冒険家 / Adventurer：穏やかで感受性に優れ、芸術的なセンスを持ちます。",
    ISFJ: "擁護者 / Defender：忠実で思いやりがあり、人を支えることが得意。",
    ISTJ: "管理者 / Logistician：責任感が強く、計画的で安定した実行者。",
    ISTP: "巨匠 / Virtuoso：実践的な問題解決者。独立心があり、柔軟に動くタイプ。",
    ENFP: "運動家 / Campaigner：情熱的で創造力にあふれ、人を惹きつける魅力の持ち主。",
    ENFJ: "主人公 / Protagonist：人を導くカリスマ性を持つリーダータイプ。",
    ENTJ: "指揮官 / Commander：生まれながらのリーダーで、効率と目標を重視。",
    ENTP: "討論者 / Debater：頭の回転が速く、常に新しいアイデアを生み出す発明家。",
    ESFP: "エンターテイナー / Entertainer：明るく社交的で、楽しさを周囲に伝えるエンターテイナー。",
    ESFJ: "領事 / Consul：親切で協力的、他者を思いやる調和の取れた人物。",
    ESTP: "起業家 / Entrepreneur：大胆で行動的。瞬時に判断し挑戦を楽しむタイプ。",
    ESTJ: "幹部 / Executive：秩序と構造を重んじ、組織を率いるマネージャー気質。"
  };
  return descriptions[type] || "個性的なユニークタイプです。";
}

const typeMatches = {
  INFP: { match: ["ENFJ", "INFJ"], reason: "価値観を尊重し合える関係です。" },
  INFJ: { match: ["ENFP", "INFP"], reason: "深い対話ができる理想的な相性です。" },
  INTJ: { match: ["ENFP", "ENTP"], reason: "論理と直感のバランスが良いです。" },
  INTP: { match: ["ENTJ", "ENFP"], reason: "知的好奇心を刺激し合える関係です。" },
  ISFP: { match: ["ESFJ", "ENFJ"], reason: "穏やかで補い合える関係です。" },
  ISFJ: { match: ["ESFP", "ESTP"], reason: "安定と刺激のバランスがとれています。" },
  ISTJ: { match: ["ESFP", "ISFJ"], reason: "責任感と柔軟性が補い合えます。" },
  ISTP: { match: ["ESFJ", "ESTJ"], reason: "お互いの行動力を支え合える関係です。" },
  ENFP: { match: ["INFJ", "INTJ"], reason: "自由さと深さが両立します。" },
  ENFJ: { match: ["INFP", "ISFP"], reason: "思いやりと感性が共鳴します。" },
  ENTJ: { match: ["INTP", "ISTP"], reason: "戦略性と柔軟性が高相性です。" },
  ENTP: { match: ["INFJ", "INTJ"], reason: "好奇心と内省性がバランスします。" },
  ESFP: { match: ["ISFJ", "ISTJ"], reason: "活発さと安定が両立します。" },
  ESFJ: { match: ["ISFP", "ISTP"], reason: "調和を重んじた関係性が築けます。" },
  ESTP: { match: ["ISFJ", "ESFJ"], reason: "行動力と支援性が補完的です。" },
  ESTJ: { match: ["ISFP", "ISTP"], reason: "リーダーシップと実行力が噛み合います。" }
};
function showMatchDetail(type) {
  const descriptions = {
    INFP: "仲介者 / Mediator：理想を追い求める仲介者。感受性が強く、他人の痛みに敏感です。",
    INFJ: "提唱者 / Advocate：内省的で直感的、人の成長を助けるカウンセラータイプ。",
    INTJ: "建築家 / Architect：戦略家で分析的。目標に向かって冷静に進むタイプ。",
    INTP: "論理学者 / Logician：理論と知識を探求する建築家タイプ。",
    ISFP: "冒険家 / Adventurer：穏やかで感受性に優れ、芸術的なセンスを持ちます。",
    ISFJ: "擁護者 / Defender：忠実で思いやりがあり、人を支えることが得意。",
    ISTJ: "管理者 / Logistician：責任感が強く、計画的で安定した実行者。",
    ISTP: "巨匠 / Virtuoso：実践的な問題解決者。独立心があり、柔軟に動くタイプ。",
    ENFP: "運動家 / Campaigner：情熱的で創造力にあふれ、人を惹きつける魅力の持ち主。",
    ENFJ: "主人公 / Protagonist：人を導くカリスマ性を持つリーダータイプ。",
    ENTJ: "指揮官 / Commander：生まれながらのリーダーで、効率と目標を重視。",
    ENTP: "討論者 / Debater：頭の回転が速く、常に新しいアイデアを生み出す発明家。",
    ESFP: "エンターテイナー / Entertainer：明るく社交的で、楽しさを周囲に伝えるエンターテイナー。",
    ESFJ: "領事 / Consul：親切で協力的、他者を思いやる調和の取れた人物。",
    ESTP: "起業家 / Entrepreneur：大胆で行動的。瞬時に判断し挑戦を楽しむタイプ。",
    ESTJ: "幹部 / Executive：秩序と構造を重んじ、組織を率いるマネージャー気質。"
  };

  const box = document.getElementById("match-details");
  const imgSrc = typeImages[type] || "images/default.png";

  box.innerHTML = `
    <div class="match-character">
      <img src="${imgSrc}" alt="${type}の画像">
      <div>
        <strong>${type}</strong><br>${descriptions[type] || "説明が見つかりません"}
      </div>
    </div>
  `;
  box.style.display = "block";
}




function tweetResult() {
  const type = getResultType();
  const text = encodeURIComponent(`MBTI診断の結果は ${type} でした！`);
  const url = encodeURIComponent(window.location.href);
  window.open(`https://twitter.com/intent/tweet?text=${text}&url=${url}`, "_blank");
}

// 初期化
showQuestion();

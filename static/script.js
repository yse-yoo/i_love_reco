// ページ読み込み時に保存されたテーマを適用
if (localStorage.getItem('theme') === 'dark') {
    document.documentElement.classList.add('dark');
} else if (localStorage.getItem('theme') === 'light') {
    document.documentElement.classList.remove('dark');
}

document.addEventListener('DOMContentLoaded', () => {
    // ===== 共通 UI要素の取得 =====
    const toggleDark = document.getElementById('toggleDark');
    const toggleDarkMobile = document.getElementById('toggleDarkMobile');
    const moodButtons = document.querySelectorAll('.mood-btn');
    const moodInput = document.getElementById('moodInput');
    const submitButton = document.querySelector('.submit-btn');
    const aiMessageDiv = document.getElementById('aiMessage');
    const aiTextSpan = document.getElementById('aiText');
    const menuToggle = document.getElementById("menuToggle");
    const mobileMenu = document.getElementById("mobileMenu");
    const closeMenu = document.getElementById("closeMenu");
    const movieContainer = document.getElementById('movieResults');
    const tipElement = document.getElementById('geminiTip');
    const refreshButton = document.getElementById('refreshTip');
    const datePicker = document.getElementById('calendarPicker');

    // ===== ダークモード切り替え =====
    [toggleDark, toggleDarkMobile].forEach(btn => {
        if (btn) {
            btn.addEventListener('click', () => {
                document.documentElement.classList.toggle('dark');
                localStorage.setItem(
                    'theme',
                    document.documentElement.classList.contains('dark') ? 'dark' : 'light'
                );
            });
        }
    });

    // ===== ハンバーガーメニュー開閉 =====
    if (menuToggle && mobileMenu && closeMenu) {
        menuToggle.addEventListener('click', () => {
            mobileMenu.classList.remove("translate-x-full");
            mobileMenu.classList.add("translate-x-0");
        });

        closeMenu.addEventListener('click', () => {
            mobileMenu.classList.remove("translate-x-0");
            mobileMenu.classList.add("translate-x-full");
        });
    }

    // ===== mood-btn の自動入力処理 =====
    if (moodButtons.length > 0 && moodInput) {
        moodButtons.forEach(button => {
            button.addEventListener('click', () => {
                const emoji = button.textContent;
                const text = button.getAttribute('data-text');
                moodInput.value = `${emoji} ${text}`;
            });
        });
    }

    // ===== AI送信ボタン処理 =====
    if (submitButton && moodInput) {
        submitButton.addEventListener('click', async () => {
            const mood = moodInput.value.trim();
            const modeElem = document.getElementById('mode');
            const mode = modeElem ? modeElem.value : 'normal';

            if (mood === "") {
                alert("気分を入力してください。");
                return;
            }

            submitButton.disabled = true;
            submitButton.textContent = '思考中...';
            submitButton.classList.add('opacity-70', 'cursor-not-allowed');

            if (aiMessageDiv) aiMessageDiv.classList.add('hidden');
            if (aiTextSpan) aiTextSpan.textContent = '';
            if (movieContainer) {
                movieContainer.classList.add('hidden');
                movieContainer.innerHTML = '';
            }

            try {
                const res = await fetch('/ai', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ mood, mode })
                });

                if (!res.ok) {
                    const errText = await res.text();
                    throw new Error(`HTTP error! status: ${res.status} / ${errText}`);
                }

                const data = await res.json();

                if (mode !== 'movie') {
                    if (aiTextSpan && data.reply) {
                        // ★ここがinnerHTMLになっていることを確認済み
                        aiTextSpan.innerHTML = data.reply.replace(/\n/g, '<br>');
                    }
                    if (aiMessageDiv) aiMessageDiv.classList.remove('hidden');
                    if (movieContainer) {
                        movieContainer.classList.add('hidden');
                        movieContainer.innerHTML = '';
                    }
                } else {
                    if (aiMessageDiv) aiMessageDiv.classList.add('hidden');
                    if (movieContainer) {
                        movieContainer.innerHTML = '';
                        if (data.movies && data.movies.length > 0) {
                            data.movies.forEach(movie => {
                                const card = document.createElement('div');
                                card.className = 'bg-slate-600 text-white dark:bg-gray-100 dark:text-gray-900 rounded p-4 shadow';
                                card.innerHTML = `
                                    <h3 class="text-xl font-bold mb-2">${movie.title || 'タイトル不明'}</h3>
                                    ${movie.poster_path ? `<img src="${movie.poster_path}" alt="${movie.title}" class="w-32 mb-2 rounded">` : ''}
                                    <p class="mb-2 text-sm">${movie.overview || 'あらすじはありません。'}</p>
                                    <p class="text-sm text-slate-300 dark:text-gray-600">公開日: ${movie.release_date || '不明'}</p>
                                    <a href="${movie.tmdb_url}" target="_blank" class="text-blue-400 hover:underline text-sm">TMDBで見る</a>
                                `;
                                movieContainer.appendChild(card);
                            });
                            movieContainer.classList.remove('hidden');
                        } else {
                            movieContainer.classList.add('hidden');
                        }
                    }
                }
            } catch (e) {
                alert('エラーが発生しました: ' + (e.message || e));
            } finally {
                submitButton.disabled = false;
                submitButton.textContent = '決定';
                submitButton.classList.remove('opacity-70', 'cursor-not-allowed');
            }
        });

        // ===== エンターキー送信 =====
        moodInput.addEventListener('keydown', function (event) {
            if (event.key === 'Enter' && !event.shiftKey) {
                event.preventDefault();
                if (!submitButton.disabled) {
                    submitButton.click();
                }
            }
        });
    }

    // ===== ログ折りたたみ（クリックイベント登録） =====
    const dateButtons = document.querySelectorAll('[data-log-toggle]');
    dateButtons.forEach(button => {
        const date = button.getAttribute('data-log-toggle');
        button.addEventListener('click', () => toggleLogs(date));
    });

    // ===== flatpickr の初期化 =====
    if (datePicker) {
        flatpickr(datePicker, {
            dateFormat: "Y-m-d",
            onChange: (selectedDates, dateStr) => {
                const allSections = document.querySelectorAll('[id^="logs-"]');
                allSections.forEach(sec => sec.classList.add('hidden'));

                const target = document.getElementById(`logs-${dateStr}`);
                if (target) {
                    target.classList.remove('hidden');
                } else {
                    alert(`この日にチャット履歴はありません: ${dateStr}`);
                }
            }
        });
    }

    const randomMoodBtn = document.getElementById('randomMoodBtn');
    const randomTexts = [
        "今日はなんだかワクワクする！", "ちょっと疲れ気味だけど頑張る！", "リラックスしてまったりしたい",
        "新しいことにチャレンジしたい気分", "おいしいもの食べたい！", "冒険に出かけたい！",
        "今日はのんびり過ごしたい", "何か楽しいことが起こりそう！", "すっきりしたい気分",
        "わくわくしたい！",
    ];

    if (randomMoodBtn && moodInput) {
        randomMoodBtn.addEventListener('click', () => {
            const randomIndex = Math.floor(Math.random() * randomTexts.length);
            const randomText = randomTexts[randomIndex];
            moodInput.value = randomText;
        });
    }
});

// ===== グローバル関数（onclick対応） =====
function toggleLogs(date) {
    const safeDate = date.replace(/-/g, '_');
    const el = document.getElementById('logs-' + safeDate);
    if (!el) return;
    el.classList.toggle('hidden');
}
window.toggleLogs = toggleLogs;

// 「近くのお店を探す」ボタンが押されたときに実行される関数
function findNearbyRestaurants(food) {
    if (!navigator.geolocation) {
        alert("このブラウザは位置情報取得に対応していません。");
        return;
    }

    const resultDivId = `restaurants_${food.replace(/\s+/g, '_')}`;
    const resultDiv = document.getElementById(resultDivId);
    if (resultDiv) {
        resultDiv.innerHTML = "<p class='text-gray-500'>近くのお店を検索中...</p>";
    }

    navigator.geolocation.getCurrentPosition(
        (position) => {
            const lat = position.coords.latitude;
            const lon = position.coords.longitude;

            fetch(`/find_restaurants?lat=${lat}&lon=${lon}&food=${encodeURIComponent(food)}`)
                .then(response => {
                    if (!response.ok) {
                        return response.json().then(errorData => {
                            throw new Error(errorData.error || `HTTPエラー: ${response.status}`);
                        });
                    }
                    return response.json();
                })
                .then(data => {
                    if (!resultDiv) return;

                    if (data.error) {
                        resultDiv.innerHTML = `<p class='text-red-500'>エラー: ${data.error}</p>`;
                        return;
                    }

                    if (data.length === 0) {
                        resultDiv.innerHTML = "<p class='text-gray-500'>近くに該当するお店が見つかりませんでした。</p>";
                        return;
                    }

                    let html = "<ul class='list-disc list-inside mt-2'>";
                    data.forEach(place => {
                        html += `
                            <li class='mb-2'>
                                <a href="${place.url}" target="_blank" class="text-blue-500 underline">${place.name}</a>
                                <p class='text-sm text-white-600'>${place.vicinity} (評価: ${place.rating})</p>
                            </li>
                        `;
                    });
                    html += "</ul>";
                    resultDiv.innerHTML = html;
                })
                .catch(error => {
                    console.error("レストラン検索エラー:", error);
                    resultDiv.innerHTML = `<p class='text-red-500'>検索中にエラーが発生しました: ${error.message || error}</p>`;
                });
        },
        (error) => {
            alert("位置情報を取得できませんでした。ブラウザの設定で位置情報の許可を確認してください。");
            if (resultDiv) {
                resultDiv.innerHTML = "";
            }
            console.error("位置情報取得エラー:", error);
        }
    );
}
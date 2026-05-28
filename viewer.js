// State
        let threadData = null;
        let currentPage = 1;
        const postsPerPage = 20;
        let isGalleryMode = false;

        // Check for file protocol warning
        if (window.location.protocol === 'file:') {
            const warningEl = document.getElementById('file-protocol-warning');
            if (warningEl) warningEl.style.display = 'block';
            const homeLink = document.getElementById('logo-home-link');
            if (homeLink) homeLink.href = '../../index.html';
        }

        // Theme management
        const themeToggle = document.getElementById('theme-toggle');
        
        function setTheme(theme) {
            document.documentElement.setAttribute('data-theme', theme);
            localStorage.setItem('theme', theme);
            themeToggle.textContent = theme === 'dark' ? 'Giao diện Sáng' : 'Giao diện Tối';
        }

        // Initialize theme
        const savedTheme = localStorage.getItem('theme') || 
            (window.matchMedia('(prefers-color-scheme: dark)').matches ? 'dark' : 'light');
        setTheme(savedTheme);

        themeToggle.addEventListener('click', () => {
            const currentTheme = document.documentElement.getAttribute('data-theme');
            setTheme(currentTheme === 'dark' ? 'light' : 'dark');
        });

        // Gallery Mode toggle listener
        const galleryToggle = document.getElementById('gallery-toggle');
        galleryToggle.addEventListener('click', () => {
            isGalleryMode = !isGalleryMode;
            
            if (isGalleryMode) {
                galleryToggle.textContent = '📖 Bình thường';
                galleryToggle.classList.add('active');
                galleryToggle.style.backgroundColor = 'var(--accent-color)';
                galleryToggle.style.color = '#ffffff';
            } else {
                galleryToggle.textContent = '🖼️ Thư viện ảnh';
                galleryToggle.classList.remove('active');
                galleryToggle.style.backgroundColor = '';
                galleryToggle.style.color = '';
            }
            
            renderUI();
        });

        // HTML Content Converter (reformats quote tags or renders clean XenForo HTML natively)
        function formatPostBody(post) {
            let bodyHtml = post.content;
            if (!bodyHtml) return "";
            
            // Check if content is HTML (contains tags) or old raw text
            if (bodyHtml.includes('<') && bodyHtml.includes('>')) {
                const tempDiv = document.createElement('div');
                tempDiv.innerHTML = bodyHtml;
                
                // 1. Remove all XenForo "Click to expand..." elements
                const expandLinks = tempDiv.querySelectorAll('.bbCodeBlock-expandLink, .bbCodeBlock-expandable-trigger');
                expandLinks.forEach(el => el.remove());
                
                // Also recursively find any text node matching "Click to expand..." and remove it
                const walker = document.createTreeWalker(tempDiv, NodeFilter.SHOW_TEXT, null, false);
                let node;
                const nodesToRemove = [];
                while (node = walker.nextNode()) {
                    if (node.nodeValue.trim() === 'Click to expand...') {
                        nodesToRemove.push(node);
                    }
                }
                nodesToRemove.forEach(n => n.parentNode && n.parentNode.removeChild(n));
                
                // Remove TikTok SVG icon inside media wrappers or links
                const ttsvgs = tempDiv.querySelectorAll('svg');
                ttsvgs.forEach(svg => {
                    if (svg.innerHTML.includes('M448,209.91') || svg.querySelector('path[d*="M448,209.91"]')) {
                        svg.remove();
                    }
                });
                
                // 2. Clean up leading/trailing whitespace and <br> tags inside quote/spoiler content blocks.
                // Uses direct text node manipulation (not innerHTML reset) to avoid detaching nested elements.
                const trimContentEl = (contentEl) => {
                    // Helper: trim leading or trailing whitespace from boundary text nodes,
                    // and remove whitespace-only text nodes and bare <br> elements at each end.
                    const trimEnd = (el, fromStart) => {
                        let changed = true;
                        while (changed && el.childNodes.length > 0) {
                            changed = false;
                            const node = fromStart ? el.firstChild : el.lastChild;
                            if (!node) break;
                            if (node.nodeType === Node.TEXT_NODE) {
                                const trimmed = fromStart
                                    ? node.nodeValue.replace(/^[\s\t\n\r]+/, '')
                                    : node.nodeValue.replace(/[\s\t\n\r]+$/, '');
                                if (trimmed === '') {
                                    node.remove();
                                    changed = true;
                                } else if (trimmed !== node.nodeValue) {
                                    node.nodeValue = trimmed;
                                    // Don't loop further — we've trimmed the boundary text
                                }
                            } else if (node.nodeType === Node.ELEMENT_NODE &&
                                       node.nodeName === 'BR') {
                                node.remove();
                                changed = true;
                            } else {
                                break;
                            }
                        }
                    };
                    trimEnd(contentEl, true);
                    trimEnd(contentEl, false);
                };

                // Target the innermost content divs (expandContent holds the actual text;
                // bbCodeBlock-content is the wrapper — process deepest first to avoid parent reset issues)
                // Also covers unfurl card elements (link title, domain row, favicon span) which share the same indentation issue.
                const elsTrimWhitespace = tempDiv.querySelectorAll(
                    '.bbCodeBlock-expandContent, .bbCodeBlock-content, ' +
                    '.contentRow-header a, .contentRow-minor, .js-unfurl-favicon'
                );
                [...elsTrimWhitespace].reverse().forEach(el => trimContentEl(el));


                // 3. Map local images if downloaded, or restore original online URL
                const imgs = tempDiv.querySelectorAll('img:not(.smilie):not(.emoji)');
                imgs.forEach((img, imgIdx) => {
                    img.classList.add('post-image-item');
                    img.setAttribute('loading', 'lazy'); // Native lazy loading
                    
                    // Bind error boundary: if local file is missing/downloading, swap to absolute online url
                    let img_src = img.getAttribute('src') || "";
                    let img_data_src = img.getAttribute('data-src') || "";
                    let img_data_url = img.getAttribute('data-url') || "";
                    
                    let originalUrl = null;
                    if (img_src.includes('proxy.php')) {
                        originalUrl = img_src;
                    } else if (img_data_src.includes('proxy.php')) {
                        originalUrl = img_data_src;
                    } else {
                        originalUrl = img_data_url || img_data_src || img_src;
                    }
                    
                    if (originalUrl && originalUrl.startsWith('data:')) {
                        originalUrl = null;
                    }
                    
                    if (originalUrl) {
                        img.onerror = function() {
                            img.onerror = null; // Prevent recursion
                            img.src = originalUrl;
                        };
                    }
                    
                    // Use local file only when the download flag was used AND this image has a filename recorded.
                    // Otherwise fall back directly to the online URL — no failed local request needed.
                    const localFilename = post.local_images && post.local_images[imgIdx];
                    if (localFilename) {
                        img.src = 'images/' + localFilename;
                    } else if (originalUrl) {
                        img.src = originalUrl;
                    }
                });

                // 4. Convert YouTube and TikTok links to responsive embedded players
                const embeddedIds = new Set();
                const links = tempDiv.querySelectorAll('a');
                
                // Helper to decode Voz redirect links (handling both base64 and standard url encoding)
                function tryDecodeRedirect(url) {
                    if (!url) return "";
                    if (url.includes('redirect?to=')) {
                        try {
                            const urlObj = new URL(url);
                            let toParam = urlObj.searchParams.get('to') || "";
                            if (toParam) {
                                // Try base64 decoding first
                                try {
                                    let decodedBase64 = atob(decodeURIComponent(toParam));
                                    if (decodedBase64.startsWith('http://') || decodedBase64.startsWith('https://')) {
                                        return decodedBase64;
                                    }
                                } catch (e) {}
                                // Try standard URL decoding
                                let decodedUrl = decodeURIComponent(toParam);
                                if (decodedUrl.startsWith('http://') || decodedUrl.startsWith('https://')) {
                                    return decodedUrl;
                                }
                            }
                        } catch (e) {}
                    }
                    return url;
                }

                function extractYoutubeId(str) {
                    if (!str) return null;
                    let match = str.match(/youtube\.com\/shorts\/([^"&?\/ ]{11})/i);
                    if (match) return match[1];
                    match = str.match(/(?:youtube\.com\/(?:[^\/]+\/.+\/|(?:v|e(?:mbed)?)\/|.*[?&]v=)|youtu\.be\/)([^"&?\/ ]{11})/i);
                    return match ? match[1] : null;
                }

                function extractTiktokId(str) {
                    if (!str) return null;
                    const match = str.match(/tiktok\.com\/(?:@[^\/]+\/)?video\/(\d+)/i);
                    return match ? match[1] : null;
                }

                links.forEach(a => {
                    const rawHref = a.getAttribute('href') || "";
                    const decodedHref = tryDecodeRedirect(rawHref);
                    const textContent = a.textContent.trim();
                    
                    // Check both the resolved link URL and visible text
                    const ytId = extractYoutubeId(decodedHref) || extractYoutubeId(textContent);
                    if (ytId) {
                        if (!embeddedIds.has(ytId)) {
                            embeddedIds.add(ytId);
                            
                            const header = document.createElement('div');
                            header.className = 'media-header';
                            header.innerHTML = `
                                <span class="media-title">📺 Video YouTube</span>
                                <a href="https://www.youtube.com/watch?v=${ytId}" target="_blank" class="media-link">Xem trên YouTube ↗</a>
                            `;
                            
                            const wrapper = document.createElement('div');
                            wrapper.className = 'bbMediaWrapper has-header';
                            wrapper.innerHTML = `
                                <div class="bbMediaWrapper-inner">
                                    <iframe src="https://www.youtube.com/embed/${ytId}" 
                                            allowfullscreen="true" 
                                            allow="accelerometer; autoplay; clipboard-write; encrypted-media; gyroscope; picture-in-picture; web-share" 
                                            referrerpolicy="strict-origin-when-cross-origin"
                                            loading="lazy"></iframe>
                                </div>
                            `;
                            a.parentNode.insertBefore(header, a.nextSibling);
                            header.parentNode.insertBefore(wrapper, header.nextSibling);
                        }
                    }
                    
                    const ttId = extractTiktokId(decodedHref) || extractTiktokId(textContent);
                    if (ttId) {
                        if (!embeddedIds.has(ttId)) {
                            embeddedIds.add(ttId);
                            
                            const header = document.createElement('div');
                            header.className = 'media-header tiktok-header';
                            header.innerHTML = `
                                <span class="media-title">🎵 Video TikTok</span>
                                <a href="https://www.tiktok.com/video/${ttId}" target="_blank" class="media-link">Xem trên TikTok ↗</a>
                            `;
                            
                            const wrapper = document.createElement('div');
                            wrapper.className = 'bbMediaWrapper tiktok-embed-wrapper has-header';
                            wrapper.innerHTML = `
                                <div class="bbMediaWrapper-inner tiktok-inner">
                                    <iframe src="https://www.tiktok.com/embed/v2/${ttId}" 
                                            allowfullscreen="true" 
                                            allow="autoplay; encrypted-media"
                                            loading="lazy"></iframe>
                                </div>
                            `;
                            a.parentNode.insertBefore(header, a.nextSibling);
                            header.parentNode.insertBefore(wrapper, header.nextSibling);
                        }
                    }
                });

                // 5. Identify and optimize existing XenForo Facebook Unfurl blocks
                const unfurls = tempDiv.querySelectorAll('.bbCodeBlock--unfurl');
                unfurls.forEach(unfurl => {
                    const link = unfurl.querySelector('a');
                    if (link) {
                        const rawHref = link.getAttribute('href') || "";
                        const decodedHref = tryDecodeRedirect(rawHref);
                        if (decodedHref.includes('facebook.com')) {
                            unfurl.className = 'bbCodeBlock bbCodeBlock--unfurl bbCodeBlock--unfurl-facebook';
                            
                            // Remove description, meta details, and minor details (like favicons/domains)
                            const desc = unfurl.querySelector('.bbCodeBlock-unfurl-desc');
                            if (desc) desc.remove();
                            const meta = unfurl.querySelector('.bbCodeBlock-unfurl-meta');
                            if (meta) meta.remove();
                            const minor = unfurl.querySelector('.contentRow-minor');
                            if (minor) minor.remove();
                            
                            // Re-construct the premium Facebook meta row
                            const mainDiv = unfurl.querySelector('.contentRow-main');
                            if (mainDiv) {
                                // Add clean meta row
                                const metaRow = document.createElement('div');
                                metaRow.className = 'facebook-meta-row';
                                metaRow.innerHTML = `
                                    <svg class="facebook-favicon" viewBox="0 0 24 24" fill="#1877f2" xmlns="http://www.w3.org/2000/svg">
                                        <path d="M24 12.073c0-6.627-5.373-12-12-12s-12 5.373-12 12c0 5.99 4.388 10.954 10.125 11.854v-8.385H7.078v-3.47h3.047V9.43c0-3.007 1.792-4.669 4.533-4.669 1.312 0 2.686.235 2.686.235v2.953H15.83c-1.491 0-1.956.925-1.956 1.874v2.25h3.328l-.532 3.47h-2.796v8.385C19.612 23.027 24 18.062 24 12.073z"/>
                                    </svg>
                                    <span>www.facebook.com</span>
                                `;
                                mainDiv.appendChild(metaRow);
                            }
                            
                            // Check if figure contains a generic logo and remove it
                            const figure = unfurl.querySelector('.contentRow-figure');
                            if (figure) {
                                const img = figure.querySelector('img');
                                if (img) {
                                    const src = img.getAttribute('src') || "";
                                    // If it's a generic brand logo or favicon, remove the figure entirely
                                    if (src.includes('favicon') || (src.includes('facebook') && src.includes('icon'))) {
                                        figure.remove();
                                    }
                                }
                            }
                        }
                    }
                });

                // 6. Convert plain Facebook links to beautiful minimal card unfurls (without generic logo)
                const fbLinks = tempDiv.querySelectorAll('a');
                fbLinks.forEach(a => {
                    if (a.closest('.bbCodeBlock--unfurl')) return;
                    
                    const rawHref = a.getAttribute('href') || "";
                    const decodedHref = tryDecodeRedirect(rawHref);
                    const isFacebook = decodedHref.includes('facebook.com') || a.textContent.includes('facebook.com');
                    
                    if (isFacebook) {
                        const card = document.createElement('div');
                        card.className = 'bbCodeBlock bbCodeBlock--unfurl bbCodeBlock--unfurl-facebook';
                        card.style.cursor = 'pointer';
                        card.addEventListener('click', () => {
                            window.open(decodedHref || rawHref, '_blank');
                        });
                        
                        card.innerHTML = `
                            <div class="contentRow">
                                <div class="contentRow-main">
                                    <h3 class="bbCodeBlock-unfurl-title">
                                        <a href="${decodedHref || rawHref}" target="_blank" onclick="event.stopPropagation();">${a.textContent.trim() || 'Liên kết Facebook'}</a>
                                    </h3>
                                    <div class="facebook-meta-row">
                                        <svg class="facebook-favicon" viewBox="0 0 24 24" fill="#1877f2" xmlns="http://www.w3.org/2000/svg">
                                            <path d="M24 12.073c0-6.627-5.373-12-12-12s-12 5.373-12 12c0 5.99 4.388 10.954 10.125 11.854v-8.385H7.078v-3.47h3.047V9.43c0-3.007 1.792-4.669 4.533-4.669 1.312 0 2.686.235 2.686.235v2.953H15.83c-1.491 0-1.956.925-1.956 1.874v2.25h3.328l-.532 3.47h-2.796v8.385C19.612 23.027 24 18.062 24 12.073z"/>
                                        </svg>
                                        <span>www.facebook.com</span>
                                    </div>
                                </div>
                            </div>
                        `;
                        a.parentNode.replaceChild(card, a);
                    }
                });

                return tempDiv.innerHTML;
            }
            
            // Fallback: It is plain text (from older pre-HTML test runs). Parse text-only quotes.
            const lines = bodyHtml.split('\n');
            let formatted = [];
            let inQuote = false;
            let quoteAuthor = "";
            let quoteContent = [];

            for (let line of lines) {
                if (line.trim().endsWith('said:')) {
                    if (inQuote) {
                        formatted.push(buildQuoteHtml(quoteAuthor, quoteContent.join('\n')));
                        quoteContent = [];
                    }
                    inQuote = true;
                    quoteAuthor = line.trim();
                } else if (inQuote && (line.trim() === 'Click to expand...' || line.trim() === 'Click to expand...')) {
                    // skip expand line
                } else if (inQuote && (line.startsWith('\t') || line.startsWith('			') || line.startsWith('    '))) {
                    quoteContent.push(line.trim());
                } else {
                    if (inQuote) {
                        formatted.push(buildQuoteHtml(quoteAuthor, quoteContent.join('\n')));
                        inQuote = false;
                        quoteAuthor = "";
                        quoteContent = [];
                    }
                    formatted.push(escapeHtml(line));
                }
            }

            if (inQuote) {
                formatted.push(buildQuoteHtml(quoteAuthor, quoteContent.join('\n')));
            }

            return formatted.join('\n');
        }

        function buildQuoteHtml(author, content) {
            return `
                <div class="bbCodeBlock">
                    <div class="bbCodeBlock-title">${escapeHtml(author)}</div>
                    <div class="bbCodeBlock-content">${escapeHtml(content)}</div>
                </div>
            `;
        }

        function escapeHtml(text) {
            return text
                .replace(/&/g, "&amp;")
                .replace(/</g, "&lt;")
                .replace(/>/g, "&gt;")
                .replace(/"/g, "&quot;")
                .replace(/'/g, "&#039;");
        }

        function getReactionEmoji(type) {
            const map = {
                "Like": "👍",
                "1": "👍",
                "Ưng": "⭐",
                "12": "⭐",
                "Haha": "😆",
                "Love": "❤️",
                "Sad": "😢",
                "Angry": "😡"
            };
            return map[type] || "👍";
        }

        // Render Posts and UI components
        let searchQuery = '';

        function getFilteredComments() {
            if (!threadData || !threadData.comments) return [];
            if (!searchQuery) return threadData.comments;
            const query = searchQuery.toLowerCase().trim();
            return threadData.comments.filter(c => {
                const authorMatch = c.author && c.author.toLowerCase().includes(query);
                const contentMatch = c.content && c.content.toLowerCase().includes(query);
                return authorMatch || contentMatch;
            });
        }

        // Pinterest view utilities
        function getCleanSnippet(htmlContent) {
            if (!htmlContent) return "";
            
            // Check if it's raw text or HTML
            if (!htmlContent.includes('<') && !htmlContent.includes('>')) {
                const text = htmlContent.replace(/\s+/g, ' ').trim();
                if (text.length > 120) {
                    return text.substring(0, 120) + '...';
                }
                return text;
            }

            const temp = document.createElement('div');
            temp.innerHTML = htmlContent;
            
            // Remove blockquotes, spoilers, media headers, media wrappers, and Facebook cards
            const elementsToRemove = temp.querySelectorAll(
                '.bbCodeBlock, .bbCodeSpoiler, .media-header, .bbMediaWrapper, ' +
                '.bbCodeBlock--unfurl, .reactionsBar'
            );
            elementsToRemove.forEach(el => el.remove());
            
            let text = temp.textContent || temp.innerText || "";
            text = text.replace(/\s+/g, ' ').trim();
            if (text.length > 120) {
                return text.substring(0, 120) + '...';
            }
            return text;
        }

        function renderGallery(posts) {
            const container = document.getElementById('posts-container');
            container.innerHTML = '';
            
            if (posts.length === 0) {
                container.innerHTML = '<div style="text-align: center; padding: 40px; color: var(--text-muted); font-weight: 500;">Không có bài viết nào chứa hình ảnh phù hợp.</div>';
                return;
            }
            
            const grid = document.createElement('div');
            grid.className = 'gallery-grid';
            
            posts.forEach((post) => {
                const initials = post.author ? post.author.charAt(0).toUpperCase() : '?';
                const snippet = getCleanSnippet(post.content);
                
                // Get the first image as cover
                let coverSrc = "";
                let hasCover = false;
                if (post.images && post.images.length > 0) {
                    coverSrc = post.images[0];
                    if (post.local_images && post.local_images[0]) {
                        coverSrc = 'images/' + post.local_images[0];
                    }
                    hasCover = true;
                }
                
                // Setup images fallback onerror handler similar to standard posts
                let originalUrl = post.images && post.images[0];
                let onerrorHtml = "";
                if (originalUrl) {
                    onerrorHtml = `onerror="this.onerror=null; this.src='${originalUrl}';"`;
                }
                
                // Multiple images badge
                let badgeHtml = '';
                if (post.images && post.images.length > 1) {
                    badgeHtml = `<div class="gallery-card-badge">+${post.images.length - 1} ảnh</div>`;
                }
                
                // Setup reaction icons
                let reactionsHtml = '';
                if (post.reactions && post.reactions.text) {
                    reactionsHtml += '<div class="gallery-card-reactions">';
                    if (post.reactions.icons && post.reactions.icons.length > 0) {
                        reactionsHtml += '<div class="gallery-card-reaction-emojis">';
                        post.reactions.icons.slice(0, 3).forEach(ico => {
                            reactionsHtml += `<span class="gallery-card-reaction-emoji">${getReactionEmoji(ico)}</span>`;
                        });
                        reactionsHtml += '</div>';
                    }
                    let simplifiedText = post.reactions.text;
                    if (simplifiedText.length > 20) {
                        simplifiedText = simplifiedText.substring(0, 20) + '...';
                    }
                    reactionsHtml += `<span class="gallery-card-reaction-text" title="${escapeHtml(post.reactions.text)}">${escapeHtml(simplifiedText)}</span>`;
                    reactionsHtml += '</div>';
                }
                
                const card = document.createElement('div');
                card.className = 'gallery-card';
                card.onclick = () => goToPost(post.post_id, post.page);
                
                let imgHtml = '';
                if (hasCover) {
                    imgHtml = `
                        <div class="gallery-card-img-wrapper">
                            <img src="${coverSrc}" class="gallery-card-img" alt="Post cover" loading="lazy" ${onerrorHtml}>
                            ${badgeHtml}
                        </div>
                    `;
                }
                
                card.innerHTML = `
                    ${imgHtml}
                    <div class="gallery-card-content">
                        <div class="gallery-card-author">
                            <div class="gallery-card-avatar">${initials}</div>
                            <div class="gallery-card-meta">
                                <span class="gallery-card-username">${escapeHtml(post.author)}</span>
                                <span class="gallery-card-time">${escapeHtml(post.time || 'Không rõ ngày')}</span>
                            </div>
                        </div>
                        ${snippet ? `<div class="gallery-card-snippet">${snippet}</div>` : ''}
                        <div class="gallery-card-footer">
                            ${reactionsHtml}
                            <span class="gallery-card-id-tag">Trang ${post.page || '?'}</span>
                        </div>
                    </div>
                `;
                
                grid.appendChild(card);
            });
            
            container.appendChild(grid);
            window.scrollTo({ top: 0, behavior: 'smooth' });
        }

        window.goToPost = function(postId, pageNum) {
            isGalleryMode = false;
            
            const toggleBtn = document.getElementById('gallery-toggle');
            toggleBtn.textContent = '🖼️ Thư viện ảnh';
            toggleBtn.classList.remove('active');
            toggleBtn.style.backgroundColor = '';
            toggleBtn.style.color = '';
            
            if (searchQuery) {
                const filtered = getFilteredComments();
                const postIndex = filtered.findIndex(c => c.post_id === postId);
                if (postIndex !== -1) {
                    currentPage = Math.floor(postIndex / postsPerPage) + 1;
                }
            } else if (pageNum) {
                currentPage = Number(pageNum);
            }
            
            renderUI();
            
            setTimeout(() => {
                const targetAnchor = document.getElementById('post-' + postId);
                if (targetAnchor) {
                    const postCard = targetAnchor.closest('.post-card');
                    if (postCard) {
                        postCard.scrollIntoView({ behavior: 'smooth', block: 'center' });
                        postCard.classList.add('highlighted-post');
                        setTimeout(() => {
                            postCard.classList.remove('highlighted-post');
                        }, 2000);
                    }
                }
            }, 150);
        };

        function renderUI() {
            if (!threadData || !threadData.comments) return;

            // Make the search box and gallery toggle visible
            document.getElementById('search-container').style.display = 'flex';
            document.getElementById('gallery-toggle').style.display = 'block';

            // Render Thread Title & Info
            document.getElementById('thread-header').style.display = 'block';
            document.getElementById('thread-title').textContent = threadData.thread_title || "Voz Archive Thread";
            
            const threadUrlLink = document.getElementById('thread-url');
            threadUrlLink.textContent = threadData.thread_url || "voz.vn";
            threadUrlLink.href = threadData.thread_url || "#";
            
            const filtered = getFilteredComments();

            if (isGalleryMode) {
                const postsWithImages = filtered.filter(c => c.images && c.images.length > 0);
                
                if (searchQuery) {
                    document.getElementById('total-comments-count').textContent = `Thư viện: Tìm thấy ${postsWithImages.length} bình luận có ảnh`;
                } else {
                    document.getElementById('total-comments-count').textContent = `Thư viện: ${postsWithImages.length} bình luận có ảnh`;
                }
                
                // Hide pagination
                document.getElementById('pagination-top').innerHTML = '';
                document.getElementById('pagination-bottom').innerHTML = '';
                
                renderGallery(postsWithImages);
                return;
            }

            if (searchQuery) {
                document.getElementById('total-comments-count').textContent = `Tìm thấy ${filtered.length} / ${threadData.comments.length} bình luận`;
            } else {
                document.getElementById('total-comments-count').textContent = `${threadData.comments.length} bình luận`;
            }

            if (searchQuery) {
                const totalPages = Math.ceil(filtered.length / postsPerPage);
                renderPostsForLocalSlice(currentPage, filtered);
                renderPagination(totalPages);
            } else {
                const comments = threadData.comments;
                const pages = Array.from(new Set(comments.map(c => Number(c.page)))).filter(p => !isNaN(p) && p > 0).sort((a,b) => a-b);
                
                if (pages.length === 0) {
                    const totalPages = Math.ceil(comments.length / postsPerPage);
                    renderPostsForLocalSlice(currentPage, comments);
                    renderPagination(totalPages);
                } else {
                    // Ensure current active page exists in the available pages array
                    if (!pages.includes(Number(currentPage))) {
                        currentPage = pages[0];
                    }
                    renderPostsForPage(currentPage);
                    renderPagination(pages[pages.length - 1], pages);
                }
            }
        }

        function renderPostsForPage(pageNumber) {
            const container = document.getElementById('posts-container');
            container.innerHTML = '';

            const pageComments = threadData.comments.filter(c => c.page === pageNumber);
            
            if (pageComments.length === 0) {
                container.innerHTML = '<div style="text-align: center; padding: 20px;">Không có bình luận nào trên trang này.</div>';
                return;
            }

            let absoluteIndex = (pageNumber - 1) * 20;

            pageComments.forEach((post, index) => {
                absoluteIndex++;
                const initials = post.author ? post.author.charAt(0).toUpperCase() : '?';
                const formattedBody = formatPostBody(post);
                
                // Render images list ONLY as fallback for older plain text runs
                let imagesHtml = '';
                const isHtml = post.content.includes('<') && post.content.includes('>');
                if (!isHtml && post.images && post.images.length > 0) {
                    imagesHtml += '<div class="post-images">';
                    post.images.forEach((imgUrl, imgIdx) => {
                        let src = imgUrl;
                        if (post.local_images && post.local_images[imgIdx]) {
                            src = 'images/' + post.local_images[imgIdx];
                        }
                        imagesHtml += `<img src="${src}" class="post-image-item" alt="Post Attachment" loading="lazy" onerror="this.onerror=null; this.src='${imgUrl}';">`;
                    });
                    imagesHtml += '</div>';
                }
                
                // Render reactions list if available
                let reactionsHtml = '';
                if (post.reactions && post.reactions.text) {
                    reactionsHtml += `<div class="reactionsBar" style="cursor: pointer;" onclick="showReactionsOverlay('${post.post_id}')">`;
                    if (post.reactions.icons && post.reactions.icons.length > 0) {
                        reactionsHtml += '<div class="reactionsBar-icons">';
                        post.reactions.icons.forEach(ico => {
                            reactionsHtml += `<span class="reaction-icon-small" title="${escapeHtml(ico)}">${getReactionEmoji(ico)}</span>`;
                        });
                        reactionsHtml += '</div>';
                    }
                    
                    // Highlight usernames in reactions text
                    let rxText = escapeHtml(post.reactions.text);
                    if (post.reactions.users && post.reactions.users.length > 0) {
                        post.reactions.users.forEach(u => {
                            const escapedU = escapeHtml(u);
                            rxText = rxText.replace(escapedU, `<a href="#">${escapedU}</a>`);
                        });
                    }
                    reactionsHtml += `<span class="reactionsBar-text">${rxText}</span>`;
                    reactionsHtml += '</div>';
                }
                
                const postCard = document.createElement('article');
                postCard.className = 'post-card';
                postCard.innerHTML = `
                    <div class="post-author-sidebar">
                        <div class="avatar">${initials}</div>
                        <div class="username">${escapeHtml(post.author)}</div>
                        <div class="user-title">Thành viên</div>
                    </div>
                    <div class="post-content-container">
                        <div class="post-header">
                            <div class="post-time">${escapeHtml(post.time || 'Không rõ ngày')}</div>
                            <a href="#post-${post.post_id}" class="post-number" id="post-${post.post_id}">#${absoluteIndex}</a>
                        </div>
                        <div class="post-body">${formattedBody}${imagesHtml}</div>
                        ${reactionsHtml}
                        <div class="post-footer">
                            <span class="action-link">Ưng</span>
                            <span class="action-link">Báo cáo</span>
                            <span class="action-link">Trích dẫn</span>
                        </div>
                    </div>
                `;
                container.appendChild(postCard);
            });

            window.scrollTo({ top: 0, behavior: 'smooth' });
        }

        function renderPostsForLocalSlice(pageNumber, sourceComments) {
            const container = document.getElementById('posts-container');
            container.innerHTML = '';

            const startIndex = (pageNumber - 1) * postsPerPage;
            const endIndex = startIndex + postsPerPage;
            const pageComments = sourceComments.slice(startIndex, endIndex);

            if (pageComments.length === 0) {
                container.innerHTML = '<div style="text-align: center; padding: 20px;">Không tìm thấy bình luận nào phù hợp.</div>';
                return;
            }

            pageComments.forEach((post, index) => {
                const absNum = startIndex + index + 1;
                const initials = post.author ? post.author.charAt(0).toUpperCase() : '?';
                const formattedBody = formatPostBody(post);
                
                // Original Page Tag when searching
                let pageTagHtml = '';
                if (searchQuery && post.page) {
                    pageTagHtml = `<span class="post-original-page" style="margin-left: 8px;">Trang ${post.page}</span>`;
                }

                // Render images list ONLY as fallback for older plain text runs
                let imagesHtml = '';
                const isHtml = post.content.includes('<') && post.content.includes('>');
                if (!isHtml && post.images && post.images.length > 0) {
                    imagesHtml += '<div class="post-images">';
                    post.images.forEach((imgUrl, imgIdx) => {
                        let src = imgUrl;
                        if (post.local_images && post.local_images[imgIdx]) {
                            src = 'images/' + post.local_images[imgIdx];
                        }
                        imagesHtml += `<img src="${src}" class="post-image-item" alt="Post Attachment" loading="lazy" onerror="this.onerror=null; this.src='${imgUrl}';">`;
                    });
                    imagesHtml += '</div>';
                }
                
                // Render reactions list if available
                let reactionsHtml = '';
                if (post.reactions && post.reactions.text) {
                    reactionsHtml += `<div class="reactionsBar" style="cursor: pointer;" onclick="showReactionsOverlay('${post.post_id}')">`;
                    if (post.reactions.icons && post.reactions.icons.length > 0) {
                        reactionsHtml += '<div class="reactionsBar-icons">';
                        post.reactions.icons.forEach(ico => {
                            reactionsHtml += `<span class="reaction-icon-small" title="${escapeHtml(ico)}">${getReactionEmoji(ico)}</span>`;
                        });
                        reactionsHtml += '</div>';
                    }
                    
                    // Highlight usernames in reactions text
                    let rxText = escapeHtml(post.reactions.text);
                    if (post.reactions.users && post.reactions.users.length > 0) {
                        post.reactions.users.forEach(u => {
                            const escapedU = escapeHtml(u);
                            rxText = rxText.replace(escapedU, `<a href="#">${escapedU}</a>`);
                        });
                    }
                    reactionsHtml += `<span class="reactionsBar-text">${rxText}</span>`;
                    reactionsHtml += '</div>';
                }
                
                const postCard = document.createElement('article');
                postCard.className = 'post-card';
                postCard.innerHTML = `
                    <div class="post-author-sidebar">
                        <div class="avatar">${initials}</div>
                        <div class="username">${escapeHtml(post.author)}</div>
                        <div class="user-title">Thành viên</div>
                    </div>
                    <div class="post-content-container">
                        <div class="post-header">
                            <div class="post-time">${escapeHtml(post.time || 'Không rõ ngày')}</div>
                            <div>
                                <a href="#post-${post.post_id}" class="post-number" id="post-${post.post_id}">#${absNum}</a>
                                ${pageTagHtml}
                            </div>
                        </div>
                        <div class="post-body">${formattedBody}${imagesHtml}</div>
                        ${reactionsHtml}
                        <div class="post-footer">
                            <span class="action-link">Ưng</span>
                            <span class="action-link">Báo cáo</span>
                            <span class="action-link">Trích dẫn</span>
                        </div>
                    </div>
                `;
                container.appendChild(postCard);
            });
            window.scrollTo({ top: 0, behavior: 'smooth' });
        }

        function renderPagination(totalPages, pagesArray = null) {
            const topNav = document.getElementById('pagination-top');
            const bottomNav = document.getElementById('pagination-bottom');
            
            totalPages = Number(totalPages);
            if (pagesArray) {
                pagesArray = pagesArray.map(Number);
            }

            if (totalPages <= 1) {
                topNav.innerHTML = '';
                bottomNav.innerHTML = '';
                return;
            }

            const buildNavHtml = () => {
                let html = '<div class="page-nav">';
                
                // Show Prev
                if (currentPage > 1) {
                    html += `<button class="page-btn" onclick="changePage(${currentPage - 1})">Trước</button>`;
                }

                // XenForo pagination layout (1, 2 ... current-1, current, current+1 ... total)
                const range = 2; // numbers to show around current page
                for (let i = 1; i <= totalPages; i++) {
                    if (pagesArray && !pagesArray.includes(i)) continue; // skip if page doesn't exist

                    if (i === 1 || i === totalPages || (i >= currentPage - range && i <= currentPage + range)) {
                        html += `<button class="page-btn ${i === currentPage ? 'active' : ''}" onclick="changePage(${i})">${i}</button>`;
                    } else if (i === currentPage - range - 1 || i === currentPage + range + 1) {
                        html += `<span style="padding: 6px; color: var(--text-muted);">...</span>`;
                    }
                }

                // Show Next
                if (currentPage < totalPages) {
                    html += `<button class="page-btn" onclick="changePage(${currentPage + 1})">Sau</button>`;
                }
                
                html += '</div>';
                return html;
            };

            const navHtml = buildNavHtml();
            topNav.innerHTML = navHtml;
            bottomNav.innerHTML = navHtml;
        }

        window.changePage = function(page) {
            currentPage = Number(page);
            if (threadData) {
                if (searchQuery) {
                    const filtered = getFilteredComments();
                    const totalPages = Math.ceil(filtered.length / postsPerPage);
                    renderPostsForLocalSlice(currentPage, filtered);
                    renderPagination(totalPages);
                } else {
                    const comments = threadData.comments;
                    const pages = Array.from(new Set(comments.map(c => Number(c.page)))).filter(p => !isNaN(p) && p > 0).sort((a,b) => a-b);
                    if (pages.length === 0) {
                        renderPostsForLocalSlice(currentPage, comments);
                        renderPagination(Math.ceil(comments.length / postsPerPage));
                    } else {
                        renderPostsForPage(currentPage);
                        renderPagination(pages[pages.length - 1], pages);
                    }
                }
            }
        };

        // Reactions popup modal controller logic
        const reactionsModal = document.getElementById('reactions-modal');
        const modalUsersList = document.getElementById('modal-users-list');
        const modalReactionsFooter = document.getElementById('modal-reactions-footer');
        const modalCloseBtn = document.getElementById('modal-close-btn');

        window.showReactionsOverlay = function(postId) {
            if (!threadData || !threadData.comments) return;
            const post = threadData.comments.find(c => c.post_id === postId);
            if (!post || !post.reactions) return;

            modalUsersList.innerHTML = '';
            
            // Build the users list in modal body
            if (post.reactions.users && post.reactions.users.length > 0) {
                post.reactions.users.forEach((u, idx) => {
                    const initials = u ? u.charAt(0).toUpperCase() : '?';
                    const userItem = document.createElement('div');
                    userItem.className = 'modal-user-item';
                    userItem.innerHTML = `
                        <div class="modal-user-avatar">${initials}</div>
                        <div class="modal-user-name">${idx + 1}. ${escapeHtml(u)}</div>
                        <div class="modal-user-role">Thành viên</div>
                    `;
                    modalUsersList.appendChild(userItem);
                });
            } else {
                modalUsersList.innerHTML = '<div style="text-align: center; padding: 20px; color: var(--text-muted);">Không có danh sách thành viên cụ thể.</div>';
            }

            // Parse footer note for "others" from the text string
            let footerText = '';
            const match = post.reactions.text.match(/(?:and|và)\s+(\d+)\s+others/i) || post.reactions.text.match(/(?:và|and)\s+(\d+)\s+người\s+khác/i);
            if (match && match[1]) {
                footerText = `Dữ liệu lưu trữ chỉ hiển thị thành viên nổi bật. Còn ${match[1]} người khác đã phản hồi bài viết này.`;
            } else {
                const total = post.reactions.users ? post.reactions.users.length : 0;
                footerText = `Tổng cộng có ${total} thành viên đã phản hồi.`;
            }
            modalReactionsFooter.textContent = footerText;

            // Activate modal
            reactionsModal.classList.add('active');
        };

        function closeReactionsModal() {
            reactionsModal.classList.remove('active');
        }

        modalCloseBtn.addEventListener('click', closeReactionsModal);
        reactionsModal.addEventListener('click', (e) => {
            if (e.target === reactionsModal) closeReactionsModal();
        });

        // Close on Escape key press
        document.addEventListener('keydown', (e) => {
            if (e.key === 'Escape' && reactionsModal.classList.contains('active')) {
                closeReactionsModal();
            }
        });

        // File loading handling
        const fileInput = document.getElementById('file-input');
        const uploadZone = document.getElementById('upload-zone');

        fileInput.addEventListener('change', (e) => {
            const file = e.target.files[0];
            if (file) handleJsonFile(file);
        });

        // Drag and drop support
        uploadZone.addEventListener('dragover', (e) => {
            e.preventDefault();
            uploadZone.style.borderColor = 'var(--accent-color)';
        });

        uploadZone.addEventListener('dragleave', () => {
            uploadZone.style.borderColor = 'var(--border-color)';
        });

        uploadZone.addEventListener('drop', (e) => {
            e.preventDefault();
            uploadZone.style.borderColor = 'var(--border-color)';
            const file = e.dataTransfer.files[0];
            if (file && file.name.endsWith('.json')) {
                handleJsonFile(file);
            }
        });

        function handleJsonFile(file) {
            const reader = new FileReader();
            document.getElementById('posts-container').innerHTML = `
                <div class="loader">
                    <div class="loader-spinner"></div>
                    Đang giải mã dữ liệu file JSON...
                </div>
            `;
            
            reader.onload = function(e) {
                try {
                    threadData = JSON.parse(e.target.result);
                    currentPage = 1;
                    renderUI();
                    uploadZone.style.display = 'none'; // hide upload zone if successful
                } catch (err) {
                    document.getElementById('posts-container').innerHTML = `
                        <div style="color: red; text-align: center; padding: 20px; font-weight: 500;">
                            Lỗi: Định dạng file JSON không hợp lệ!
                        </div>
                    `;
                }
            };
            reader.readAsText(file);
        }

        // Auto load fallback (first checks window.threadData for offline CORS bypass)
        if (window.threadData) {
            threadData = window.threadData;
            renderUI();
            uploadZone.style.display = 'none';
        } else {
            fetch('sample.json')
                .then(res => {
                    if (res.ok) return res.json();
                    throw new Error('Not found');
                })
                .then(data => {
                    threadData = data;
                    renderUI();
                    uploadZone.style.display = 'none';
                })
                .catch(() => {
                    // If sample.json doesn't exist, try loading comments.json as fallback
                    fetch('comments.json')
                        .then(res => {
                            if (res.ok) return res.json();
                            throw new Error('Not found');
                        })
                        .then(data => {
                            threadData = data;
                            renderUI();
                            uploadZone.style.display = 'none';
                        })
                        .catch(() => {
                            // Show file selection instruction if auto-load fails (e.g. offline file:// or missing files)
                            document.getElementById('posts-container').innerHTML = `
                                <div style="text-align: center; padding: 40px; color: var(--text-muted); font-weight: 500;">
                                    Hãy kéo thả hoặc chọn file dữ liệu JSON ở trên để xem bài viết.
                                </div>
                            `;
                        });
                });
        }

        // Search Input listeners
        const searchInput = document.getElementById('search-input');
        const searchClearBtn = document.getElementById('search-clear-btn');

        searchInput.addEventListener('input', (e) => {
            searchQuery = e.target.value;
            currentPage = 1; // Reset to page 1 on search key change
            
            if (searchQuery.trim()) {
                searchClearBtn.style.display = 'block';
            } else {
                searchClearBtn.style.display = 'none';
            }
            
            renderUI();
        });

        searchClearBtn.addEventListener('click', () => {
            searchInput.value = '';
            searchQuery = '';
            searchClearBtn.style.display = 'none';
            currentPage = 1;
            renderUI();
        });

        // Global click handler for XenForo elements (event delegation)
        document.addEventListener('click', (e) => {
            // Spoiler toggle click handler
            const spoilerBtn = e.target.closest('.bbCodeSpoiler-button');
            if (spoilerBtn) {
                e.preventDefault();
                const parent = spoilerBtn.closest('.bbCodeSpoiler');
                if (parent) {
                    const content = parent.querySelector('.bbCodeSpoiler-content');
                    if (content) {
                        const isHidden = content.style.display === 'none' || !content.style.display;
                        content.style.display = isHidden ? 'block' : 'none';
                        spoilerBtn.style.borderColor = isHidden ? 'var(--accent-color)' : 'var(--border-color)';
                    }
                }
            }
        });

        // --- Lightbox Media Gallery Logic ---
        let lightboxImages = [];
        let lightboxIndex = -1;
        let zoomLevel = 1;
        let isDragging = false;
        let startX, startY, translateX = 0, translateY = 0;

        // Delegated click handler inside comments container to trigger Lightbox
        const postsContainer = document.getElementById('posts-container');
        if (postsContainer) {
            postsContainer.addEventListener('click', (e) => {
                const img = e.target.closest('.post-image-item, .gallery-card-img');
                if (img) {
                    openLightbox(img);
                }
            });
        }

        function openLightbox(clickedImg) {
            // Find all visible images loaded on the page
            const imagesInDOM = Array.from(document.querySelectorAll('.post-image-item, .gallery-card-img'));
            
            // Deduplicate matching sources
            lightboxImages = [];
            const uniqueSrcs = new Set();
            
            imagesInDOM.forEach(img => {
                const src = img.getAttribute('src');
                if (src && !uniqueSrcs.has(src)) {
                    uniqueSrcs.add(src);
                    lightboxImages.push(img);
                }
            });
            
            // Find index of clicked image
            const clickedSrc = clickedImg.getAttribute('src');
            lightboxIndex = lightboxImages.findIndex(img => img.getAttribute('src') === clickedSrc);
            
            if (lightboxIndex === -1) {
                lightboxImages = [clickedImg];
                lightboxIndex = 0;
            }
            
            const modal = document.getElementById('lightbox-modal');
            if (modal) {
                modal.style.display = 'flex';
                modal.focus();
                showLightboxImage();
            }
        }

        function showLightboxImage() {
            if (lightboxIndex < 0 || lightboxIndex >= lightboxImages.length) return;
            
            const img = lightboxImages[lightboxIndex];
            const src = img.getAttribute('src');
            const lightboxImg = document.getElementById('lightbox-img');
            
            if (lightboxImg) {
                lightboxImg.src = src;
                resetLightboxZoom();
            }
            
            const caption = document.getElementById('lightbox-caption');
            if (caption) {
                caption.textContent = `Hình ảnh ${lightboxIndex + 1} / ${lightboxImages.length}`;
            }
            
            const downloadLink = document.getElementById('lightbox-download');
            if (downloadLink) {
                downloadLink.href = src;
                let filename = src.split('/').pop().split('?')[0];
                if (!filename || filename.includes('proxy.php')) {
                    filename = `image_${lightboxIndex + 1}.jpg`;
                }
                downloadLink.setAttribute('download', filename);
            }
        }

        window.changeLightboxImage = function(direction) {
            if (lightboxImages.length <= 1) return;
            lightboxIndex += direction;
            
            if (lightboxIndex < 0) {
                lightboxIndex = lightboxImages.length - 1;
            } else if (lightboxIndex >= lightboxImages.length) {
                lightboxIndex = 0;
            }
            
            showLightboxImage();
        };

        window.closeLightbox = function() {
            const modal = document.getElementById('lightbox-modal');
            if (modal) {
                modal.style.display = 'none';
            }
        };

        function applyImageTransform() {
            const lightboxImg = document.getElementById('lightbox-img');
            if (lightboxImg) {
                lightboxImg.style.transform = `translate(${translateX}px, ${translateY}px) scale(${zoomLevel})`;
            }
        }

        function zoomLightbox(amount) {
            zoomLevel = Math.max(0.5, Math.min(5, zoomLevel + amount));
            applyImageTransform();
        }

        function resetLightboxZoom() {
            zoomLevel = 1;
            translateX = 0;
            translateY = 0;
            applyImageTransform();
        }

        // Mouse Drag & Pan Handlers
        const lightboxImg = document.getElementById('lightbox-img');
        const lightboxContent = document.getElementById('lightbox-content');

        if (lightboxImg && lightboxContent) {
            lightboxImg.addEventListener('mousedown', (e) => {
                e.preventDefault();
                isDragging = true;
                startX = e.clientX - translateX;
                startY = e.clientY - translateY;
                lightboxImg.style.transition = 'none';
            });

            window.addEventListener('mousemove', (e) => {
                if (!isDragging) return;
                translateX = e.clientX - startX;
                translateY = e.clientY - startY;
                applyImageTransform();
            });

            window.addEventListener('mouseup', () => {
                if (isDragging) {
                    isDragging = false;
                    lightboxImg.style.transition = 'transform 0.1s ease';
                }
            });

            // Wheel zoom
            lightboxContent.addEventListener('wheel', (e) => {
                e.preventDefault();
                const delta = e.deltaY > 0 ? -0.15 : 0.15;
                zoomLightbox(delta);
            }, { passive: false });

            // Double click to zoom
            lightboxImg.addEventListener('dblclick', () => {
                if (zoomLevel > 1) {
                    resetLightboxZoom();
                } else {
                    zoomLevel = 2.5;
                    applyImageTransform();
                }
            });

            // Mobile Swiping Gestures
            let touchStartX = 0;
            let touchStartY = 0;

            lightboxContent.addEventListener('touchstart', (e) => {
                if (e.touches.length === 1) {
                    touchStartX = e.touches[0].clientX;
                    touchStartY = e.touches[0].clientY;
                }
            }, { passive: true });

            lightboxContent.addEventListener('touchend', (e) => {
                if (e.changedTouches.length === 1 && zoomLevel === 1) {
                    const touchEndX = e.changedTouches[0].clientX;
                    const touchEndY = e.changedTouches[0].clientY;
                    
                    const diffX = touchEndX - touchStartX;
                    const diffY = touchEndY - touchStartY;
                    
                    if (Math.abs(diffX) > 80 && Math.abs(diffY) < 100) {
                        if (diffX > 0) {
                            changeLightboxImage(-1);
                        } else {
                            changeLightboxImage(1);
                        }
                    }
                }
            }, { passive: true });
        }

        // Toolbar Button Event Bindings
        const btnZoomIn = document.getElementById('lightbox-zoom-in');
        if (btnZoomIn) btnZoomIn.addEventListener('click', () => zoomLightbox(0.25));

        const btnZoomOut = document.getElementById('lightbox-zoom-out');
        if (btnZoomOut) btnZoomOut.addEventListener('click', () => zoomLightbox(-0.25));

        const btnZoomReset = document.getElementById('lightbox-zoom-reset');
        if (btnZoomReset) btnZoomReset.addEventListener('click', resetLightboxZoom);

        // Keyboard Controls
        window.addEventListener('keydown', (e) => {
            const modal = document.getElementById('lightbox-modal');
            if (!modal || modal.style.display !== 'flex') return;
            
            if (e.key === 'ArrowLeft') {
                changeLightboxImage(-1);
            } else if (e.key === 'ArrowRight') {
                changeLightboxImage(1);
            } else if (e.key === 'Escape') {
                closeLightbox();
            } else if (e.key === '+' || e.key === '=') {
                zoomLightbox(0.2);
            } else if (e.key === '-') {
                zoomLightbox(-0.2);
            } else if (e.key === 'r' || e.key === 'R') {
                resetLightboxZoom();
            }
        });

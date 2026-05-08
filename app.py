    # --- NEWS SECTION (Final Version) ---
    st.subheader(f"Latest {ticker} News")
    ticker_obj = yf.Ticker(ticker)
    news_data = ticker_obj.news

    if news_data:
        for article in news_data[:8]:  # Show top 8
            # 1. Get the content block
            content = article.get("content", article)
            
            # 2. Extract Data
            title = content.get("title", "No Title")
            
            # Link handling: Look in 'clickThroughUrl', then 'canonicalUrl', then 'link'
            link = None
            ct_url = content.get("clickThroughUrl")
            if isinstance(ct_url, dict):
                link = ct_url.get("url")
            if not link:
                link = content.get("canonicalUrl", {}).get("url")
            if not link:
                link = article.get("link")
            
            # 3. Layout with Image and Text
            with st.container():
                col1, col2 = st.columns([1, 3])
                
                # Thumbnail Logic
                thumb = content.get("thumbnail")
                has_image = False
                if isinstance(thumb, dict):
                    res = thumb.get("resolutions", [])
                    if res and isinstance(res, list):
                        col1.image(res[0].get("url"), use_container_width=True)
                        has_image = True
                
                if not has_image:
                    col1.info("No Image")

                with col2:
                    st.write(f"**{title}**")
                    if link:
                        st.markdown(f"[🔗 Read full article]({link})")
                    else:
                        st.write("*(Link unavailable)*")
                st.divider()
    else:
        st.write("No recent news found.")
    # 4. NEWS (With Safe Images)
    st.divider()
    st.subheader(f"{ticker} Headlines")
    try:
        news = yf.Ticker(ticker).news
        for art in news[:5]:
            c = art.get("content", art)
            title = c.get('title', 'News Headline')
            link = c.get("clickThroughUrl", {}).get("url") or art.get("link")
            
            # Create two columns: one for image, one for text
            col1, col2 = st.columns([1, 4])
            
            # Safe Image Logic
            with col1:
                try:
                    thumb = c.get("thumbnail", {}).get("resolutions", [])
                    if thumb:
                        st.image(thumb[0].get("url"), use_container_width=True)
                    else:
                        st.caption("No Image")
                except:
                    st.caption("No Image")

            # Text Content
            with col2:
                st.write(f"**{title}**")
                if link: 
                    st.markdown(f"[Read Article]({link})")
            
            st.write("---")
    except:
        st.write("News feed currently unavailable.")
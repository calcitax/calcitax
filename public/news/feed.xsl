<?xml version="1.0" encoding="UTF-8"?>
<!-- Makes the RSS feed readable when someone opens it directly in a browser. -->
<xsl:stylesheet version="1.0" xmlns:xsl="http://www.w3.org/1999/XSL/Transform">
  <xsl:output method="html" encoding="UTF-8" indent="yes"/>
  <xsl:template match="/rss/channel">
    <html lang="en-CA">
      <head>
        <meta charset="utf-8"/>
        <meta name="viewport" content="width=device-width, initial-scale=1"/>
        <title>News feed | Calcitax Advisors</title>
        <link rel="icon" href="/assets/favicon.svg" type="image/svg+xml"/>
        <link rel="stylesheet" href="/assets/style.css"/>
      </head>
      <body>
        <header class="site-header">
          <div class="wrap header-row">
            <a class="brand" href="/" aria-label="Calcitax Advisors home">
              <span class="brand-mark" aria-hidden="true">C</span>
              <span class="brand-name">Calcitax <span>Advisors</span></span>
            </a>
            <nav class="nav" aria-label="Main">
              <a href="/news/">News</a>
              <a href="/guides/">Guides</a>
              <a class="btn btn-primary" href="/contact.html">Free consultation</a>
            </nav>
          </div>
        </header>
        <main>
          <section class="page-hero">
            <div class="wrap narrow">
              <p class="eyebrow">News feed</p>
              <h1>Calcitax Advisors news feed</h1>
              <p class="lead">This is our news feed for reader apps such as Feedly. To follow us, copy this page's address into your news reader, or simply <a href="/news/">read the articles on our website</a>.</p>
            </div>
          </section>
          <section class="section">
            <div class="wrap narrow">
              <div class="grid-3 news-grid" style="grid-template-columns:1fr">
                <xsl:for-each select="item">
                  <a class="card news-card">
                    <xsl:attribute name="href"><xsl:value-of select="link"/></xsl:attribute>
                    <p class="news-meta"><span><xsl:value-of select="category"/></span> · <xsl:value-of select="substring(pubDate, 6, 11)"/></p>
                    <h2><xsl:value-of select="title"/></h2>
                    <p><xsl:value-of select="description"/></p>
                    <span class="more">Read more →</span>
                  </a>
                </xsl:for-each>
              </div>
            </div>
          </section>
        </main>
      </body>
    </html>
  </xsl:template>
</xsl:stylesheet>

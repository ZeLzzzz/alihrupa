-- alihrupa never downloads anything (G-001): replace images referenced by URL with their
-- description, and report each one on stderr so alihrupa can warn about it. Raw Typst is
-- dropped too, since `#import "@preview/…"` makes Typst download the package (D-035).
local function is_remote(src)
  return src:match("^%a[%w+.-]*:") ~= nil and src:match("^file:") == nil
end

local function report(src)
  io.stderr:write("alihrupa-remote-image\t" .. src .. "\n")
end

-- An attribute value, quoted or not; the leading space keeps `src` from matching `data-src`.
local function attribute(tag, name)
  local prefix = "%s" .. name .. "%s*=%s*"
  return tag:match(prefix .. "\"([^\"]*)\"") or tag:match(prefix .. "'([^']*)'") or tag:match(prefix .. "([^%s\"'>]+)")
end

-- <img> tags written as HTML in Markdown, which pandoc keeps raw; returns the remote ones.
local function remote_html_images(html)
  local found = {}
  for tag in html:gmatch("<[Ii][Mm][Gg]%s[^>]*>") do
    local src = attribute(tag, "[Ss][Rr][Cc]")
    if src and is_remote(src) then
      report(src)
      found[#found + 1] = tag
    end
  end
  return found
end

local figures = {
  Figure = function(fig)
    local remote = nil
    fig:walk({ Image = function(img) if is_remote(img.src) then remote = img.src end end })
    if remote then
      report(remote)
      return pandoc.Para(pandoc.utils.blocks_to_inlines(fig.caption.long))
    end
  end,
}

local images = {
  Image = function(img)
    if is_remote(img.src) then
      report(img.src)
      return img.caption
    end
  end,
}

local raw = {
  RawInline = function(el)
    local format = el.format:lower()
    if format == "typst" then
      io.stderr:write("alihrupa-raw-typst\n")
      return {}
    end
    if format:match("^html") then
      local tags = remote_html_images(el.text)
      if #tags > 0 then
        return pandoc.Str(attribute(tags[1], "[Aa][Ll][Tt]") or "")
      end
    end
  end,
  RawBlock = function(el)
    local format = el.format:lower()
    if format == "typst" then
      io.stderr:write("alihrupa-raw-typst\n")
      return {}
    end
    if format:match("^html") then
      remote_html_images(el.text) -- the writers drop raw HTML blocks; only report what is lost
    end
  end,
}

return { figures, images, raw }

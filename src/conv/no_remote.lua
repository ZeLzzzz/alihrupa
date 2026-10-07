-- conv never downloads anything (G-001): replace images referenced by URL with their
-- description, and report each one on stderr so conv can warn about it.
local function is_remote(src)
  return src:match("^%a[%w+.-]*:") ~= nil and src:match("^file:") == nil
end

local function report(src)
  io.stderr:write("conv-remote-image\t" .. src .. "\n")
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

return { figures, images }

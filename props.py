"""Property names on `document`'s prototype chain, from Chrome Canary 158, Firefox Nightly 161 and
Safari TP (Object.getOwnPropertyNames of each prototype), grouped by where they're defined."""

DOCUMENT_COMMON = """
implementation URL documentURI compatMode characterSet charset inputEncoding contentType doctype
documentElement xmlEncoding xmlVersion xmlStandalone domain referrer cookie lastModified readyState
title dir body head images embeds plugins links forms scripts currentScript defaultView designMode
onreadystatechange anchors applets fgColor linkColor vlinkColor alinkColor bgColor all
scrollingElement onpointerlockchange onpointerlockerror hidden visibilityState onvisibilitychange
timeline fullscreenEnabled fullscreen onfullscreenchange onfullscreenerror rootElement
activeViewTransition pictureInPictureEnabled onabort onbeforeinput onbeforematch onbeforetoggle
onblur oncancel oncanplay oncanplaythrough onchange onclick onclose oncommand
oncontentvisibilityautostatechange oncontextlost oncontextmenu oncontextrestored oncuechange
ondblclick ondrag ondragend ondragenter ondragleave ondragover ondragstart ondrop ondurationchange
onemptied onended onerror onfocus onformdata oninput oninvalid onkeydown onkeypress onkeyup onload
onloadeddata onloadedmetadata onloadstart onmousedown onmouseenter onmouseleave onmousemove
onmouseout onmouseover onmouseup onpause onplay onplaying onprogress onratechange onreset onresize
onscroll onscrollend onsecuritypolicyviolation onseeked onseeking onselect onslotchange onstalled
onsubmit onsuspend ontimeupdate ontoggle onvolumechange onwaiting onwebkitanimationend
onwebkitanimationiteration onwebkitanimationstart onwebkittransitionend onwheel onauxclick
ongotpointercapture onlostpointercapture onpointerdown onpointermove onpointerup onpointercancel
onpointerover onpointerout onpointerenter onpointerleave onselectstart onselectionchange
onanimationcancel onanimationend onanimationiteration onanimationstart ontransitionrun
ontransitionstart ontransitionend ontransitioncancel oncopy oncut onpaste children
firstElementChild lastElementChild childElementCount activeElement styleSheets pointerLockElement
fullscreenElement adoptedStyleSheets pictureInPictureElement customElementRegistry fonts
fragmentDirective adoptNode append captureEvents caretPositionFromPoint caretRangeFromPoint clear
close createAttribute createAttributeNS createCDATASection createComment createDocumentFragment
createElement createElementNS createEvent createExpression createNSResolver createNodeIterator
createProcessingInstruction createRange createTextNode createTreeWalker elementFromPoint
elementsFromPoint evaluate execCommand exitFullscreen exitPictureInPicture exitPointerLock
getAnimations getElementById getElementsByClassName getElementsByName getElementsByTagName
getElementsByTagNameNS getSelection hasFocus hasStorageAccess importNode moveBefore open prepend
queryCommandEnabled queryCommandIndeterm queryCommandState queryCommandSupported queryCommandValue
querySelector querySelectorAll releaseEvents replaceChildren requestStorageAccess
startViewTransition write writeln ariaNotify
""".split()

DOCUMENT_ENGINE_SPECIFIC = """
wasDiscarded prerendering featurePolicy webkitVisibilityState webkitHidden onbeforecopy
onbeforecut onbeforepaste onfreeze onprerenderingchange onresume onsearch webkitIsFullScreen
webkitCurrentFullScreenElement webkitFullscreenEnabled webkitFullscreenElement
onwebkitfullscreenchange onwebkitfullscreenerror onmousewheel onbeforexrselect
hasUnpartitionedCookieAccess webkitCancelFullScreen webkitExitFullscreen onscrollsnapchange
onscrollsnapchanging webkitFullScreenKeyboardInputAllowed onwebkitmouseforcechanged
onwebkitmouseforcedown onwebkitmouseforcewillbegin onwebkitmouseforceup getCSSCanvasContext
releaseCapture mozSetImageElement mozCancelFullScreen enableStyleSheetsForSet mozFullScreen
mozFullScreenEnabled selectedStyleSheetSet lastStyleSheetSet preferredStyleSheetSet
styleSheetSets mozFullScreenElement onmozfullscreenchange onmozfullscreenerror
""".split()

NODE = """
nodeType nodeName baseURI isConnected ownerDocument parentNode parentElement childNodes firstChild
lastChild previousSibling nextSibling nodeValue textContent ELEMENT_NODE ATTRIBUTE_NODE TEXT_NODE
CDATA_SECTION_NODE ENTITY_REFERENCE_NODE ENTITY_NODE PROCESSING_INSTRUCTION_NODE COMMENT_NODE
DOCUMENT_NODE DOCUMENT_TYPE_NODE DOCUMENT_FRAGMENT_NODE NOTATION_NODE
DOCUMENT_POSITION_DISCONNECTED DOCUMENT_POSITION_PRECEDING DOCUMENT_POSITION_FOLLOWING
DOCUMENT_POSITION_CONTAINS DOCUMENT_POSITION_CONTAINED_BY
DOCUMENT_POSITION_IMPLEMENTATION_SPECIFIC appendChild cloneNode compareDocumentPosition contains
getRootNode hasChildNodes insertBefore isDefaultNamespace isEqualNode isSameNode
lookupNamespaceURI lookupPrefix normalize removeChild replaceChild
""".split()

EVENT_TARGET = "addEventListener dispatchEvent removeEventListener when".split()

OBJECT = """
constructor __defineGetter__ __defineSetter__ hasOwnProperty __lookupGetter__ __lookupSetter__
isPrototypeOf propertyIsEnumerable toString valueOf __proto__ toLocaleString
""".split()

# Category per name, first match wins: Object.prototype names also appear as `constructor` on
# every interface prototype.
CATEGORY = {}
for cat, names in [
    ("Object", OBJECT),
    ("EventTarget", EVENT_TARGET),
    ("Node", NODE),
    ("Document", DOCUMENT_COMMON),
    ("Document (engine-specific)", DOCUMENT_ENGINE_SPECIFIC),
]:
    for n in names:
        CATEGORY.setdefault(n, cat)


def kind(name):
    """'attribute' (incl. constants and event handlers) or 'method', per Chrome/Firefox/Safari."""
    return "method" if name in METHODS else "attribute"


METHODS = set(
    """
adoptNode append captureEvents caretPositionFromPoint caretRangeFromPoint clear close
createAttribute createAttributeNS createCDATASection createComment createDocumentFragment
createElement createElementNS createEvent createExpression createNSResolver createNodeIterator
createProcessingInstruction createRange createTextNode createTreeWalker elementFromPoint
elementsFromPoint evaluate execCommand exitFullscreen exitPictureInPicture exitPointerLock
getAnimations getElementById getElementsByClassName getElementsByName getElementsByTagName
getElementsByTagNameNS getSelection hasFocus hasStorageAccess importNode moveBefore open prepend
queryCommandEnabled queryCommandIndeterm queryCommandState queryCommandSupported queryCommandValue
querySelector querySelectorAll releaseEvents replaceChildren requestStorageAccess
startViewTransition write writeln ariaNotify hasUnpartitionedCookieAccess webkitCancelFullScreen
webkitExitFullscreen getCSSCanvasContext releaseCapture mozSetImageElement mozCancelFullScreen
enableStyleSheetsForSet appendChild cloneNode compareDocumentPosition contains getRootNode
hasChildNodes insertBefore isDefaultNamespace isEqualNode isSameNode lookupNamespaceURI
lookupPrefix normalize removeChild replaceChild addEventListener dispatchEvent
removeEventListener when __defineGetter__ __defineSetter__ hasOwnProperty __lookupGetter__
__lookupSetter__ isPrototypeOf propertyIsEnumerable toString valueOf toLocaleString
""".split()
)

#!/usr/bin/env python

from gimpfu import *
import gtk
import os

def image_fst_diff(img, drawable):
  active_layer = pdb.gimp_image_get_active_layer(img)
  if active_layer is None:
    pdb.gimp_message("Please select a layer.")
    return

  if not len(active_layer.children):
    do_fst_diff(img, [active_layer])
  else:
    visibility = active_layer.visible
    active_layer.visible = True
    do_fst_diff(img, active_layer.children)
    active_layer.visible = visibility

def do_fst_diff(img, layers):
  pdb.gimp_image_undo_group_start(img)
  try:
    # Get background image
    visibility = [c.visible for c in layers]
    for c in layers:
      c.visible = False
    pdb.gimp_selection_all(img)
    name = pdb.gimp_edit_named_copy_visible(img, "image-fst-tmp")

    # Create temp image
    tmpimg = pdb.gimp_image_new(img.width, img.height, RGB)

    left = 99999
    top = 99999
    right = -99999
    bottom = -99999

    for c in layers:
      pdb.gimp_selection_none(tmpimg)

      # Create temp image layers
      background = pdb.gimp_layer_new(tmpimg, tmpimg.width, tmpimg.height, RGB_IMAGE, "BG", 100, NORMAL_MODE)
      foreground = pdb.gimp_layer_new(tmpimg, tmpimg.width, tmpimg.height, RGB_IMAGE, c.name + "#tmp", 100, DIFFERENCE_MODE)
      foreground2 = pdb.gimp_layer_new(tmpimg, tmpimg.width, tmpimg.height, RGBA_IMAGE, c.name, 100, NORMAL_MODE)
      pdb.gimp_image_insert_layer(tmpimg, background, None, 0)
      pdb.gimp_image_insert_layer(tmpimg, foreground, None, 0)
      pdb.gimp_image_insert_layer(tmpimg, foreground2, None, 0)

      # Paste background image
      floating = pdb.gimp_edit_named_paste(background, name, True)
      pdb.gimp_floating_sel_anchor(floating)

      # Paste image with the layer visible (twice)
      c.visible = True
      name2 = pdb.gimp_edit_named_copy_visible(img, "image-fst-tmp-2")
      floating = pdb.gimp_edit_named_paste(foreground, name2, True)
      pdb.gimp_floating_sel_anchor(floating)
      floating = pdb.gimp_edit_named_paste(foreground2, name2, True)
      pdb.gimp_floating_sel_anchor(floating)
      pdb.gimp_buffer_delete(name2)
      c.visible = False

      # Merge the two layers and threshold
      merged = pdb.gimp_image_merge_down(tmpimg, foreground, CLIP_TO_IMAGE)
      pdb.gimp_threshold(merged, 1, 255)

      # Expand the white area
      pdb.gimp_image_select_color(tmpimg, CHANNEL_OP_REPLACE, merged, (255, 255, 255))
      # pdb.gimp_selection_grow(tmpimg, 5)

      # Set the selection as mask
      mask = pdb.gimp_layer_create_mask(foreground2, ADD_SELECTION_MASK)
      pdb.gimp_layer_add_mask(foreground2, mask)
      pdb.gimp_layer_set_edit_mask(foreground2, False)

      # Remove the temporary background image
      pdb.gimp_image_remove_layer(tmpimg, merged)

      (foo, l, t, r, b) = pdb.gimp_selection_bounds(tmpimg)
      left = min(left, l)
      top = min(top, t)
      right = max(right, r)
      bottom = max(bottom, b)

    for l in tmpimg.layers:
      pdb.gimp_layer_resize(l, right - left, bottom - top, -left, -top)
    pdb.gimp_image_crop(tmpimg, right - left, bottom - top, left, top)

    print("(%d., %d., %d., %d., [])," % (left, top, right - left, bottom - top))

    pdb.gimp_display_new(tmpimg)
    # pdb.gimp_image_delete(tmpimg)
    pdb.gimp_buffer_delete(name)

    pdb.gimp_selection_all(tmpimg)
    pdb.gimp_image_clean_all(tmpimg)

    for idx, c in enumerate(layers):
      c.visible = visibility[idx]
  finally:
    pdb.gimp_image_undo_group_end(img)

register(
  "image-fst-diff",
  "Difference images of sublayers",
  "Creates difference images of each sublayer",
  "Johannes",
  "(C) 2015",
  "03/31/2015",
  "<Image>/Layer/Difference images of sublayers",
  "*",
  [],
  [],
  image_fst_diff
)

main()

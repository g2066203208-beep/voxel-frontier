#include "vf/render/VulkanRenderer.hpp"

// The V14 renderer remains the implementation authority.  Renaming only the class token lets the
// public adapter add streaming ecology without duplicating or regressing the mature Vulkan code.
#define VulkanRenderer VulkanRendererV14
#include "VulkanRendererV14.inc"
#undef VulkanRenderer

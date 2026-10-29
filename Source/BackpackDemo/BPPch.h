#pragma once
// UE 5.0 + MSVC 14.51 shim: newer MSVC ships <sanitizer/asan_interface.h>, which sends
// ConcurrentLinearAllocator.h into a __has_feature() branch that MSVC cannot parse.
#ifndef __has_feature
#define __has_feature(x) 0
#endif
#include "CoreMinimal.h"
#include "Engine.h"

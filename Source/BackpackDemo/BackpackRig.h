#pragma once
#include "CoreMinimal.h"
#include "Components/SceneComponent.h"
#include "BackpackRig.generated.h"

// One rigid piece of the backpack: a scaled cube parented to exactly one bone.
struct FRigPiece
{
	class UStaticMeshComponent* Mesh = nullptr;
	FName Bone;
	FString Name;
	FTransform BindRelative;   // relative-to-bone transform captured at bind; must never change
	FVector BaseScale;
};

// Seam between two pieces on different bones: the world distance between two local end points.
struct FRigSeam
{
	FString Name;
	int32 A = 0, B = 0;
	FVector LocalA, LocalB;    // points in each piece's mesh space
};

// The technique: segmented rigid straps + socketed rigid pack + bounded spring sway.
// Nothing here is cloth or physics-simulated.
UCLASS()
class URigBackpack : public USceneComponent
{
	GENERATED_BODY()
public:
	URigBackpack();
	virtual void TickComponent(float Dt, ELevelTick TickType, FActorComponentTickFunction* ThisTickFunction) override;

	bool Bind(class USkeletalMeshComponent* Body);   // build the pieces from the current pose
	bool IsBound() const { return bBound; }
	void SetEquipped(bool bOn);                       // 0.25 s scale beat
	bool IsEquipped() const { return bEquipped; }

	// Checks for the ledger.
	bool CheckAttachments(FString& Out) const;        // every piece still on its own bone, transform unchanged
	float MaxSeamGap(FString& Worst) const;            // cm
	float PeakPitch = 0.f, PeakRoll = 0.f;            // sway peaks since last reset (deg)
	void ResetPeaks() { PeakPitch = PeakRoll = 0.f; }
	FString Describe() const;
	static float OverlapCm();

	static constexpr float SwayClampDeg = 7.f;

private:
	UPROPERTY() class USkeletalMeshComponent* Body = nullptr;
	UPROPERTY() class USceneComponent* SwayPivot = nullptr;
	TArray<FRigPiece> Pieces;
	TArray<FRigSeam> Seams;
	FQuat PivotBase = FQuat::Identity;
	bool bBound = false, bEquipped = true;
	float EquipAlpha = 1.f;   // 0..1 current scale factor
	// spring state
	FVector PrevLoc = FVector::ZeroVector, PrevVel = FVector::ZeroVector, Accel = FVector::ZeroVector;
	float Pitch = 0.f, Roll = 0.f, PitchVel = 0.f, RollVel = 0.f;
	bool bHavePrev = false;

	int32 AddBox(const FString& Name, FName Bone, const FVector& LocalA, const FVector& LocalB,
		float Width, float Thick, const FLinearColor& Color, const FTransform& ActorTM, class USceneComponent* Parent = nullptr);
	int32 AddBlock(const FString& Name, FName Bone, const FVector& LocalCenter, const FVector& SizeCm,
		const FLinearColor& Color, const FTransform& ActorTM, class USceneComponent* Parent);
	class UStaticMeshComponent* MakeCube(const FLinearColor& Color);
};

#include "BackpackRig.h"
#include "Components/SkeletalMeshComponent.h"
#include "Components/StaticMeshComponent.h"
#include "Materials/MaterialInstanceDynamic.h"
#include "Misc/CommandLine.h"

namespace
{
	// Fit knobs (cm), overridable as -BP<Name>=value so fitting never needs a rebuild.
	struct FFit
	{
		float Front = 13.f, Back = 12.f, ShoulderUp = 7.f, Spread = 0.72f, ChestDrop = 26.f;
		FString BackBone = TEXT("spine_05"); // back straps ride the upper spine: short lever to the clavicle
		float Tuck = 5.f;
		float Overlap = 6.f;                 // bridge runs this far past each strap end, hiding clavicle drift                    // back strap runs this far under the pack lid
		float StrapW = 7.f, StrapT = 1.6f, PackDepth = 20.f, PackW = 34.f, PackH = 46.f, PackZ = -6.f, SwayK = 0.004f;
		void Load()
		{
			const TCHAR* C = FCommandLine::Get();
			FParse::Value(C, TEXT("BPFront="), Front); FParse::Value(C, TEXT("BPBack="), Back);
			FParse::Value(C, TEXT("BPShoulderUp="), ShoulderUp); FParse::Value(C, TEXT("BPSpread="), Spread);
			FParse::Value(C, TEXT("BPChestDrop="), ChestDrop); FParse::Value(C, TEXT("BPStrapW="), StrapW);
			FParse::Value(C, TEXT("BPPackDepth="), PackDepth); FParse::Value(C, TEXT("BPPackW="), PackW);
			FParse::Value(C, TEXT("BPPackH="), PackH); FParse::Value(C, TEXT("BPPackZ="), PackZ);
			FParse::Value(C, TEXT("BPSwayK="), SwayK);
			FParse::Value(C, TEXT("BPBackBone="), BackBone); FParse::Value(C, TEXT("BPTuck="), Tuck); FParse::Value(C, TEXT("BPOverlap="), Overlap);
		}
	};
	FFit Fit;
	const FName Chest(TEXT("spine_05")), Spine(TEXT("spine_03")), Neck(TEXT("neck_01"));
	const FName Clav[2] = { TEXT("clavicle_l"), TEXT("clavicle_r") };
	const FName UpperArm[2] = { TEXT("upperarm_l"), TEXT("upperarm_r") };
}

URigBackpack::URigBackpack()
{
	PrimaryComponentTick.bCanEverTick = true;
	PrimaryComponentTick.TickGroup = TG_PostUpdateWork; // after animation, so the sway reads this frame's pose
}

UStaticMeshComponent* URigBackpack::MakeCube(const FLinearColor& Color)
{
	UStaticMeshComponent* M = NewObject<UStaticMeshComponent>(GetOwner());
	M->SetStaticMesh(LoadObject<UStaticMesh>(nullptr, TEXT("/Engine/BasicShapes/Cube.Cube")));
	M->SetMaterial(0, LoadObject<UMaterialInterface>(nullptr, TEXT("/Engine/BasicShapes/BasicShapeMaterial.BasicShapeMaterial")));
	M->SetCollisionEnabled(ECollisionEnabled::NoCollision); // no strap/clothing collision at all, by design
	M->SetCastShadow(true);
	M->RegisterComponent();
	if (UMaterialInstanceDynamic* MID = M->CreateAndSetMaterialInstanceDynamic(0)) MID->SetVectorParameterValue(TEXT("Color"), Color);
	return M;
}

int32 URigBackpack::AddBox(const FString& Name, FName Bone, const FVector& LA, const FVector& LB, float Width, float Thick,
	const FLinearColor& Color, const FTransform& ActorTM, USceneComponent* Parent)
{
	const FVector A = ActorTM.TransformPosition(LA), B = ActorTM.TransformPosition(LB);
	const FVector Dir = B - A;
	UStaticMeshComponent* M = MakeCube(Color);
	const FQuat Q = FRotationMatrix::MakeFromXY(Dir.GetSafeNormal(), ActorTM.GetUnitAxis(EAxis::Y)).ToQuat();
	M->SetWorldTransform(FTransform(Q, (A + B) * 0.5f, FVector(Dir.Size() / 100.f, Width / 100.f, Thick / 100.f)));
	if (Parent) M->AttachToComponent(Parent, FAttachmentTransformRules::KeepWorldTransform);
	else M->AttachToComponent(Body, FAttachmentTransformRules::KeepWorldTransform, Bone);
	FRigPiece P; P.Mesh = M; P.Bone = Bone; P.Name = Name; P.BindRelative = M->GetRelativeTransform(); P.BaseScale = P.BindRelative.GetScale3D();
	return Pieces.Add(P);
}

int32 URigBackpack::AddBlock(const FString& Name, FName Bone, const FVector& LC, const FVector& Size, const FLinearColor& Color,
	const FTransform& ActorTM, USceneComponent* Parent)
{
	UStaticMeshComponent* M = MakeCube(Color);
	M->SetWorldTransform(FTransform(ActorTM.GetRotation(), ActorTM.TransformPosition(LC), Size / 100.f));
	M->AttachToComponent(Parent, FAttachmentTransformRules::KeepWorldTransform);
	FRigPiece P; P.Mesh = M; P.Bone = Bone; P.Name = Name; P.BindRelative = M->GetRelativeTransform(); P.BaseScale = P.BindRelative.GetScale3D();
	return Pieces.Add(P);
}

bool URigBackpack::Bind(USkeletalMeshComponent* InBody)
{
	Body = InBody;
	Fit.Load();
	for (FName B : { Chest, Spine, Neck, Clav[0], Clav[1], UpperArm[0], UpperArm[1] })
		if (Body->GetBoneIndex(B) == INDEX_NONE) { UE_LOG(LogTemp, Error, TEXT("BP: missing bone %s"), *B.ToString()); return false; }

	// Work in the character's frame: x forward, y right, z up.
	const FTransform ActorTM = GetOwner()->GetActorTransform();
	auto L = [&](FName B) { return ActorTM.InverseTransformPosition(Body->GetSocketLocation(B)); };
	const FVector S5 = L(Chest), S3 = L(Spine), N = L(Neck);
	const FLinearColor StrapC(0.025f, 0.025f, 0.03f), BridgeC(0.06f, 0.06f, 0.07f);
	const FLinearColor PackC(0.16f, 0.24f, 0.07f), OuterC(0.95f, 0.38f, 0.05f), FlapC(0.10f, 0.15f, 0.04f);

	// Pack: rigid prop on a pivot socketed at spine_03 (pivot = top-front edge where it rests on the back).
	const float PackTop = S3.Z + Fit.PackZ + Fit.PackH * 0.5f;
	const FVector PivotLocal(S3.X - Fit.Back, 0.f, PackTop);
	SwayPivot = NewObject<USceneComponent>(GetOwner());
	SwayPivot->RegisterComponent();
	SwayPivot->SetWorldTransform(FTransform(ActorTM.GetRotation(), ActorTM.TransformPosition(PivotLocal)));
	SwayPivot->AttachToComponent(Body, FAttachmentTransformRules::KeepWorldTransform, Spine);
	PivotBase = SwayPivot->GetRelativeRotation().Quaternion();
	const float Cx = S3.X - Fit.Back - Fit.PackDepth * 0.5f, Cz = S3.Z + Fit.PackZ;
	const int32 PackBody = AddBlock(TEXT("pack body"), Spine, FVector(Cx, 0, Cz), FVector(Fit.PackDepth, Fit.PackW, Fit.PackH), PackC, ActorTM, SwayPivot);
	AddBlock(TEXT("pack outer panel"), Spine, FVector(Cx - Fit.PackDepth * 0.5f - 1.5f, 0, Cz - 2.f), FVector(3.f, Fit.PackW * 0.82f, Fit.PackH * 0.78f), OuterC, ActorTM, SwayPivot);
	AddBlock(TEXT("pack lid"), Spine, FVector(Cx - 1.f, 0, Cz + Fit.PackH * 0.5f + 2.f), FVector(Fit.PackDepth + 4.f, Fit.PackW + 2.f, 5.f), FlapC, ActorTM, SwayPivot);

	for (int32 s = 0; s < 2; ++s)
	{
		const FVector UA = L(UpperArm[s]);
		const float Y = FMath::Lerp(N.Y, UA.Y, Fit.Spread);
		const float TopZ = UA.Z + Fit.ShoulderUp;
		const FString Side = s == 0 ? TEXT("L") : TEXT("R");
		// Front panel: shoulder top-front down the chest, on the chest bone.
		const FVector FrontTop(S5.X + Fit.Front * 0.55f, Y, TopZ - 3.f), FrontBot(S5.X + Fit.Front, Y * 0.92f, S5.Z - Fit.ChestDrop);
		const int32 F = AddBox(TEXT("front strap ") + Side, Chest, FrontTop, FrontBot, Fit.StrapW, Fit.StrapT, StrapC, ActorTM);
		// Bridge: over the shoulder, on the clavicle; Overlap cm past each end so the overlap hides any seam.
		const FVector BackTop(S5.X - Fit.Back * 0.55f, Y, TopZ - 3.f);
		const FVector BridgeF = FrontTop + FVector(Fit.Overlap, 0, 0), BridgeB = BackTop - FVector(Fit.Overlap, 0, 0);
		const int32 Br = AddBox(TEXT("shoulder bridge ") + Side, Clav[s], BridgeF + FVector(0, 0, 2.f), BridgeB + FVector(0, 0, 2.f), Fit.StrapW + 0.6f, Fit.StrapT + 0.4f, BridgeC, ActorTM);
		// Back panel: shoulder top-back down to the pack lid, on the spine bone.
		const FVector BackBot(S3.X - Fit.Back - 1.f, Y * 0.85f, PackTop - Fit.Tuck);
		const int32 Bk = AddBox(TEXT("back strap ") + Side, FName(*Fit.BackBone), BackTop, BackBot, Fit.StrapW, Fit.StrapT, StrapC, ActorTM);

		// Seams: shared world points at bind, re-measured every check. Gap at bind is 0 by construction.
		auto Seam = [&](const FString& Name, int32 A, int32 B, const FVector& LocalPointActor)
		{
			const FVector W = ActorTM.TransformPosition(LocalPointActor);
			FRigSeam S; S.Name = Name; S.A = A; S.B = B;
			S.LocalA = Pieces[A].Mesh->GetComponentTransform().InverseTransformPosition(W);
			S.LocalB = Pieces[B].Mesh->GetComponentTransform().InverseTransformPosition(W);
			Seams.Add(S);
		};
		Seam(TEXT("front/bridge ") + Side, F, Br, FrontTop);
		Seam(TEXT("bridge/back ") + Side, Br, Bk, BackTop);
		Seam(TEXT("back strap/pack ") + Side, Bk, PackBody, BackBot);
	}
	bBound = true;
	PrevLoc = Body->GetSocketLocation(Spine); bHavePrev = false;
	return true;
}

void URigBackpack::SetEquipped(bool bOn) { bEquipped = bOn; }

void URigBackpack::TickComponent(float Dt, ELevelTick TickType, FActorComponentTickFunction* F)
{
	Super::TickComponent(Dt, TickType, F);
	if (!bBound || Dt <= 0.f) return;

	// Equip beat: 0.25 s scale up/down. Pieces stay parented to their bones throughout.
	const float Target = bEquipped ? 1.f : 0.f;
	if (EquipAlpha != Target)
	{
		EquipAlpha = FMath::FInterpConstantTo(EquipAlpha, Target, Dt, 4.f);
		for (FRigPiece& P : Pieces)
		{
			P.Mesh->SetRelativeScale3D(P.BaseScale * FMath::Max(EquipAlpha, 0.001f));
			P.Mesh->SetVisibility(EquipAlpha > 0.f);
		}
	}

	// Bounded secondary motion: spring lag driven by the spine_03 acceleration, clamped to +/-7 deg.
	const FVector Loc = Body->GetSocketLocation(Spine);
	const FVector Vel = (Loc - PrevLoc) / Dt;
	if (bHavePrev) Accel = FMath::Lerp(Accel, (Vel - PrevVel) / Dt, FMath::Min(1.f, Dt * 12.f));
	PrevLoc = Loc; PrevVel = Vel; bHavePrev = true;
	const FVector A = GetOwner()->GetActorTransform().InverseTransformVector(Accel);
	const float TP = FMath::Clamp(-A.X * Fit.SwayK + A.Z * Fit.SwayK * 0.5f, -SwayClampDeg, SwayClampDeg);
	const float TR = FMath::Clamp(A.Y * Fit.SwayK, -SwayClampDeg, SwayClampDeg);
	const float K = 60.f, D = 9.f;
	PitchVel += (K * (TP - Pitch) - D * PitchVel) * Dt; Pitch += PitchVel * Dt;
	RollVel += (K * (TR - Roll) - D * RollVel) * Dt; Roll += RollVel * Dt;
	if (FMath::Abs(Pitch) > SwayClampDeg) { Pitch = FMath::Sign(Pitch) * SwayClampDeg; PitchVel = 0.f; }
	if (FMath::Abs(Roll) > SwayClampDeg) { Roll = FMath::Sign(Roll) * SwayClampDeg; RollVel = 0.f; }
	SwayPivot->SetRelativeRotation(PivotBase * FQuat(FRotator(Pitch, 0.f, Roll)));
	PeakPitch = FMath::Max(PeakPitch, FMath::Abs(Pitch));
	PeakRoll = FMath::Max(PeakRoll, FMath::Abs(Roll));
}

bool URigBackpack::CheckAttachments(FString& Out) const
{
	bool bOk = SwayPivot && SwayPivot->GetAttachSocketName() == Spine && SwayPivot->GetAttachParent() == Body;
	if (!bOk) Out += TEXT("pivot not on spine_03; ");
	for (const FRigPiece& P : Pieces)
	{
		const bool bOnPivot = P.Mesh->GetAttachParent() == SwayPivot;
		const bool bParentOk = bOnPivot || (P.Mesh->GetAttachParent() == Body && P.Mesh->GetAttachSocketName() == P.Bone);
		const FTransform R = P.Mesh->GetRelativeTransform();
		const bool bRigid = R.GetLocation().Equals(P.BindRelative.GetLocation(), 0.01f) && R.GetRotation().Equals(P.BindRelative.GetRotation(), 1e-4f);
		if (!bParentOk || !bRigid) { bOk = false; Out += FString::Printf(TEXT("%s %s; "), *P.Name, !bParentOk ? TEXT("reparented") : TEXT("moved off bind")); }
	}
	return bOk;
}

float URigBackpack::MaxSeamGap(FString& Worst) const
{
	float Max = 0.f;
	for (const FRigSeam& S : Seams)
	{
		const FVector WA = Pieces[S.A].Mesh->GetComponentTransform().TransformPosition(S.LocalA);
		const FVector WB = Pieces[S.B].Mesh->GetComponentTransform().TransformPosition(S.LocalB);
		const float G = FVector::Dist(WA, WB);
		if (G > Max) { Max = G; Worst = S.Name; }
	}
	return Max;
}

float URigBackpack::OverlapCm() { return Fit.Overlap; }

FString URigBackpack::Describe() const
{
	FString S;
	for (const FRigPiece& P : Pieces) S += FString::Printf(TEXT("  %-18s -> %s\n"), *P.Name, *P.Bone.ToString());
	return S;
}

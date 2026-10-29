#include "BPDemoGameMode.h"
#include "BackpackRig.h"
#include "Camera/CameraActor.h"
#include "GameFramework/Character.h"
#include "GameFramework/CharacterMovementComponent.h"
#include "Components/SkeletalMeshComponent.h"
#include "Components/CapsuleComponent.h"
#include "UObject/ConstructorHelpers.h"
#include "UnrealClient.h"
#include "Misc/CommandLine.h"
#include "Misc/FileHelper.h"
#include "Misc/Paths.h"
#include "HAL/FileManager.h"
#include "Framework/Application/SlateApplication.h"

// ---- controller: E toggles the pack, C toggles crouch ----
void ABPDemoController::SetupInputComponent()
{
	Super::SetupInputComponent();
	InputComponent->BindKey(EKeys::E, IE_Pressed, this, &ABPDemoController::ToggleEquip);
	InputComponent->BindKey(EKeys::C, IE_Pressed, this, &ABPDemoController::ToggleCrouch);
}
void ABPDemoController::ToggleEquip() { if (ABPDemoGameMode* G = GetWorld()->GetAuthGameMode<ABPDemoGameMode>()) G->ToggleEquip(TEXT("key E via PlayerController")); }
void ABPDemoController::ToggleCrouch()
{
	ACharacter* C = Cast<ACharacter>(GetPawn());
	if (ABPDemoGameMode* G = GetWorld()->GetAuthGameMode<ABPDemoGameMode>()) G->SetCrouch(!(C && C->bIsCrouched));
}

// ---- beats ----
struct FBeat { const TCHAR* Name; float Len; FVector Cam; FVector Look; const TCHAR* Shot; float ShotAt; };
static const FBeat Beats[] = {
	{ TEXT("run, front 3/4 camera"),          6.f, FVector( 250, 130,  50), FVector(0, 0, 45), TEXT("01_front_run.png"),  3.5f },
	{ TEXT("jump, side/rear camera"),         6.f, FVector( -90, 330,  60), FVector(0, 0, 40), TEXT("02_back_jump.png"), -1.f }, // shot at first jump apex
	{ TEXT("crouch (stand-in), front-side camera"),5.f, FVector( 140, 330,  60), FVector(0, 0, 10), TEXT("03_crouch.png"),     3.0f },
	{ TEXT("back view idle -> run"),          7.f, FVector(-330,  50,  90), FVector(0, 0, 40), TEXT("04_back_view.png"),  5.5f },
	{ TEXT("unequip (key E)"),                4.f, FVector(-250, 210,  70), FVector(0, 0, 40), TEXT("05_unequipped.png"), 1.5f },
	{ TEXT("equip (key E)"),                  3.f, FVector(-250, 210,  70), FVector(0, 0, 40), nullptr,                   -1.f },
};
static constexpr int32 NumBeats = UE_ARRAY_COUNT(Beats);

static void InjectKey(const FKey& Key, uint32 Char)
{
	// Same Slate entry point the Windows message pump feeds; routed to the viewport -> PlayerController.
	FSlateApplication::Get().ProcessKeyDownEvent(FKeyEvent(Key, FModifierKeysState(), 0, false, Char, Char));
	FSlateApplication::Get().ProcessKeyUpEvent(FKeyEvent(Key, FModifierKeysState(), 0, false, Char, Char));
}

ABPDemoGameMode::ABPDemoGameMode()
{
	PrimaryActorTick.bCanEverTick = true;
	static ConstructorHelpers::FClassFinder<APawn> PawnBP(TEXT("/Game/ThirdPerson/Blueprints/BP_ThirdPersonCharacter"));
	if (PawnBP.Class) DefaultPawnClass = PawnBP.Class;
	PlayerControllerClass = ABPDemoController::StaticClass();
}

ACharacter* ABPDemoGameMode::Hero() const
{
	APlayerController* PC = GetWorld()->GetFirstPlayerController();
	return PC ? Cast<ACharacter>(PC->GetPawn()) : nullptr;
}

FString ABPDemoGameMode::Dir() const { return FPaths::ProjectDir() / TEXT("Deliverables"); }

void ABPDemoGameMode::Ledger(const FString& Line)
{
	const FString L = FString::Printf(TEXT("[t=%6.2fs] %s"), Clock, *Line);
	UE_LOG(LogTemp, Display, TEXT("BP: %s"), *L);
	LedgerText += L + TEXT("\n");
}

void ABPDemoGameMode::Shoot(const TCHAR* Name)
{
	IFileManager::Get().MakeDirectory(*Dir(), true);
	FScreenshotRequest::RequestScreenshot(Dir() / Name, false, false);
	Ledger(FString::Printf(TEXT("  capture %s"), Name));
}

bool ABPDemoGameMode::TryBind()
{
	ACharacter* C = Hero();
	if (!C || Rig) return Rig != nullptr;
	Rig = NewObject<URigBackpack>(C);
	Rig->RegisterComponent();
	if (!Rig->Bind(C->GetMesh())) { Ledger(TEXT("BIND FAIL: a required bone is missing (see log)")); return false; }
	MeshBaseRot = C->GetMesh()->GetRelativeRotation().Quaternion();
	MeshBaseLoc = C->GetMesh()->GetRelativeLocation();
	C->GetCharacterMovement()->GetNavAgentPropertiesRef().bCanCrouch = true;
	Ledger(FString::Printf(TEXT("BIND OK on %s. Pieces (each rigid on exactly one bone):\n%s"), *C->GetMesh()->SkeletalMesh->GetName(), *Rig->Describe()));
	Cam = GetWorld()->SpawnActor<ACameraActor>(C->GetActorLocation(), FRotator::ZeroRotator);
	return true;
}

void ABPDemoGameMode::ToggleEquip(const TCHAR* Source)
{
	if (!Rig) return;
	Rig->SetEquipped(!Rig->IsEquipped());
	Ledger(FString::Printf(TEXT("  %s -> %s (0.25 s scale beat)"), Source, Rig->IsEquipped() ? TEXT("EQUIP") : TEXT("UNEQUIP")));
}

void ABPDemoGameMode::SetCrouch(bool bOn)
{
	ACharacter* C = Hero();
	if (!C) return;
	// Stand-in crouch: engine Crouch() shrinks the capsule and offsets the mesh; we add a forward torso pitch.
	float Lean = 20.f; FParse::Value(FCommandLine::Get(), TEXT("BPLean="), Lean);
	if (bOn) { C->Crouch(); { const FVector Axis = MeshBaseRot.Inverse().RotateVector(FVector::RightVector); C->GetMesh()->SetRelativeRotation(MeshBaseRot * FQuat(Axis, FMath::DegreesToRadians(Lean))); } }
	else { C->UnCrouch(); C->GetMesh()->SetRelativeRotation(MeshBaseRot); }
	bCrouched = bOn;
	Ledger(FString::Printf(TEXT("  crouch %s (bIsCrouched=%d capsule half-height=%.1f, torso pitch stand-in %.0f deg)"), bOn ? TEXT("ON") : TEXT("OFF"), C->bIsCrouched, C->GetCapsuleComponent()->GetUnscaledCapsuleHalfHeight(), bOn ? Lean : 0.f));
}

void ABPDemoGameMode::StartBeat(int32 B)
{
	Beat = B; BeatClock = 0.f; bShotDone = false; bJumped = false; CamFrames = 0;
	MaxGapBeat = 0.f; WorstSeam.Reset();
	if (Rig) Rig->ResetPeaks();
	if (B < NumBeats) { CamLocal = Beats[B].Cam; LookLocal = Beats[B].Look; Ledger(FString::Printf(TEXT("BEAT %d START: %s"), B + 1, Beats[B].Name)); }
}

void ABPDemoGameMode::EndBeat()
{
	FString Why;
	const bool bAttached = Rig->CheckAttachments(Why);
	const bool bSway = Rig->PeakPitch <= URigBackpack::SwayClampDeg + 0.01f && Rig->PeakRoll <= URigBackpack::SwayClampDeg + 0.01f;
	const bool bSeams = MaxGapBeat < URigBackpack::OverlapCm(); // drift inside the overlap never opens a visible gap
	bool bState = true; FString StateNote;
	if (Beat == 4) { bState = !Rig->IsEquipped(); StateNote = bState ? TEXT(" unequipped=yes") : TEXT(" unequipped=NO"); }
	if (Beat == 5) { bState = Rig->IsEquipped(); StateNote = bState ? TEXT(" re-equipped=yes") : TEXT(" re-equipped=NO"); }
	const bool bPass = bAttached && bSway && bSeams && bState;
	Ledger(FString::Printf(TEXT("BEAT %d END: %s | attached+rigid=%s%s | max seam drift=%.2f cm (%s; overlap %.0f cm) | sway peak pitch=%.2f roll=%.2f deg (clamp 7)%s | AUTO %s"),
		Beat + 1, Beats[Beat].Name, bAttached ? TEXT("yes") : TEXT("NO"), bAttached ? TEXT("") : *(TEXT(" [") + Why + TEXT("]")),
		MaxGapBeat, WorstSeam.IsEmpty() ? TEXT("-") : *WorstSeam, URigBackpack::OverlapCm(), Rig->PeakPitch, Rig->PeakRoll, *StateNote, bPass ? TEXT("PASS") : TEXT("FAIL")));
}

void ABPDemoGameMode::Drive(float Dt)
{
	ACharacter* C = Hero();
	const FBeat& B = Beats[Beat];
	BeatClock += Dt;
	// Run on a circle of radius 450 around the start so the template map's blocks stay out of the way.
	static FVector Center = C->GetActorLocation() + FVector(0, 450, 0);
	auto Run = [&]() {
		FVector R = C->GetActorLocation() - Center; R.Z = 0;
		const FVector Tangent = FVector::CrossProduct(FVector::UpVector, R.GetSafeNormal());
		C->AddMovementInput((Tangent + R.GetSafeNormal() * ((450.f - R.Size()) / 300.f)).GetSafeNormal(), 1.f);
	};
	switch (Beat)
	{
	case 0: Run(); break;
	case 1: Run();
		if (!bJumped && BeatClock > 1.0f) { C->Jump(); bJumped = true; Ledger(TEXT("  jump")); }
		if (BeatClock > 3.5f && BeatClock < 3.6f) C->Jump();
		if (!bShotDone && bJumped && BeatClock > 1.3f && C->GetCharacterMovement()->IsFalling() && C->GetVelocity().Z < 60.f) { Shoot(B.Shot); bShotDone = true; }
		break;
	case 2: if (BeatClock > 0.3f && !bCrouched) SetCrouch(true); break;
	case 3: if (BeatClock > 2.5f) Run(); break;
	case 4: if (BeatClock > 0.3f && Rig->IsEquipped()) { Ledger(TEXT("  inject key E via Slate")); InjectKey(EKeys::E, 'E'); } break;
	case 5: if (BeatClock > 0.3f && !Rig->IsEquipped()) { Ledger(TEXT("  inject key E via Slate")); InjectKey(EKeys::E, 'E'); } break;
	}
	if (B.Shot && B.ShotAt > 0.f && !bShotDone && BeatClock >= B.ShotAt && CamFrames > 20) { Shoot(B.Shot); bShotDone = true; }
	// Seams only mean something while the pack is at full scale.
	if (Rig->IsEquipped() && Beat != 5)
	{
		FString W; const float G = Rig->MaxSeamGap(W);
		if (G > MaxGapBeat) { MaxGapBeat = G; WorstSeam = W; }
	}
	if (BeatClock >= B.Len)
	{
		if (Beat == 2) SetCrouch(false);
		EndBeat();
		StartBeat(Beat + 1);
	}
}

void ABPDemoGameMode::Tick(float Dt)
{
	Super::Tick(Dt);
	Clock += Dt; ++Frames;
	if (!Rig) { if (Frames > 15) TryBind(); return; }
	ACharacter* C = Hero();
	APlayerController* PC = GetWorld()->GetFirstPlayerController();
	if (!C || !PC) return;

	// Follow camera in the character's frame; set every frame because possession resets the view target.
	const FTransform TM = C->GetActorTransform();
	static float CamScale = [](){ float S = 0.62f; FParse::Value(FCommandLine::Get(), TEXT("BPCamScale="), S); return S; }();
	const FVector Eye = TM.TransformPosition(FVector(CamLocal.X * CamScale, CamLocal.Y * CamScale, CamLocal.Z * 0.8f + 25.f)), At = TM.TransformPosition(LookLocal + FVector(0, 0, 20.f));
	Cam->SetActorLocationAndRotation(Eye, (At - Eye).Rotation());
	if (PC->GetViewTarget() != Cam) { PC->SetViewTarget(Cam); CamFrames = 0; }
	++CamFrames;

	if (!FParse::Param(FCommandLine::Get(), TEXT("BPAutoPlay"))) return;
	if (Beat < 0) { Ledger(TEXT("AUTOPLAY START")); StartBeat(0); }
	if (Beat < NumBeats) { Drive(Dt); return; }
	if (Beat == NumBeats)
	{
		Ledger(TEXT("AUTOPLAY END"));
		IFileManager::Get().MakeDirectory(*Dir(), true);
		FFileHelper::SaveStringToFile(LedgerText, *(Dir() / TEXT("BackpackLedger.txt")));
		++Beat; BeatClock = 0.f;
	}
	if ((BeatClock += Dt) > 1.5f) FGenericPlatformMisc::RequestExit(false);
}

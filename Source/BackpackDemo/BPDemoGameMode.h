#pragma once
#include "CoreMinimal.h"
#include "GameFramework/GameModeBase.h"
#include "GameFramework/PlayerController.h"
#include "BPDemoGameMode.generated.h"

UCLASS()
class ABPDemoController : public APlayerController
{
	GENERATED_BODY()
protected:
	virtual void SetupInputComponent() override;
	void ToggleEquip();
	void ToggleCrouch();
};

UCLASS()
class ABPDemoGameMode : public AGameModeBase
{
	GENERATED_BODY()
public:
	ABPDemoGameMode();
	virtual void Tick(float Dt) override;
	void ToggleEquip(const TCHAR* Source);
	void SetCrouch(bool bOn);

private:
	UPROPERTY() class URigBackpack* Rig = nullptr;
	UPROPERTY() class ACameraActor* Cam = nullptr;
	class ACharacter* Hero() const;
	bool TryBind();

	// Autoplay cycle (-BPAutoPlay): one beat per entry.
	int32 Beat = -1; float BeatClock = 0.f, Clock = 0.f; int32 Frames = 0, CamFrames = 0;
	bool bShotDone = false, bJumped = false, bCrouched = false;
	FVector CamLocal = FVector(320, 140, 70); FVector LookLocal = FVector(0, 0, 40);
	FQuat MeshBaseRot = FQuat::Identity; FVector MeshBaseLoc = FVector::ZeroVector;
	float MaxGapBeat = 0.f; FString WorstSeam;
	void StartBeat(int32 B);
	void EndBeat();
	void Drive(float Dt);
	void Shoot(const TCHAR* Name);
	void Ledger(const FString& Line);
	FString LedgerText;
	FString Dir() const;
};

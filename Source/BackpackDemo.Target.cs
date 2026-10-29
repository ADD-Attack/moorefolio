using UnrealBuildTool;
public class BackpackDemoTarget : TargetRules {
	public BackpackDemoTarget(TargetInfo Target) : base(Target) {
		Type = TargetType.Game; DefaultBuildSettings = BuildSettingsVersion.V2;
		ExtraModuleNames.Add("BackpackDemo");
	}
}

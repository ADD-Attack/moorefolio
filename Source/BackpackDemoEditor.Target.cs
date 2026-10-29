using UnrealBuildTool;
public class BackpackDemoEditorTarget : TargetRules {
	public BackpackDemoEditorTarget(TargetInfo Target) : base(Target) {
		Type = TargetType.Editor; DefaultBuildSettings = BuildSettingsVersion.V2;
		ExtraModuleNames.Add("BackpackDemo");
	}
}

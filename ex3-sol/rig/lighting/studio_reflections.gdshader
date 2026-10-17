shader_type sky;
// Reflection-only studio. Visible background is Environment.BG_COLOR.
float card(vec3 d, vec3 n, vec3 right, float w, float h) {
    float f = dot(d, n);
    vec2 uv = vec2(dot(d, right), dot(d, cross(n, right))) / max(f, 0.001);
    vec2 edge = smoothstep(vec2(w, h), vec2(w + 0.07, h + 0.07), abs(uv));
    return (1.0 - edge.x) * (1.0 - edge.y) * step(0.0, f);
}
void sky() {
    vec3 d = normalize(EYEDIR);
    float up = smoothstep(-0.45, 0.8, d.y);
    vec3 base = mix(vec3(0.035, 0.043, 0.052), vec3(0.30, 0.33, 0.37), up);
    vec3 n1 = normalize(vec3(-0.4, 0.8, 0.5));
    vec3 r1 = normalize(cross(vec3(0.,1.,0.), n1));
    vec3 n2 = normalize(vec3(0.4, 0.5, -0.8));
    vec3 r2 = normalize(cross(vec3(0.,1.,0.), n2));
    COLOR = base + vec3(1.7,1.6,1.45) * card(d,n1,r1,0.8,0.30)
                 + vec3(0.70,0.85,1.05) * card(d,n2,r2,0.65,0.13);
}

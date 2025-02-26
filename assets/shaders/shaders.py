######################################################
# Minimap shader with orthographic projection and derivative-based normal calculation
minimap_shader = {
    "vertex_shader" : '''
        #version 330 core
        layout(location = 0) in vec3 vertexPosition;

        uniform mat4 modelMatrix;
        uniform mat4 viewMatrix;
        uniform mat4 orthoProjectionMatrix;
        
        out vec3 fragmentPosition;
        out vec4 v_clip_pos;

        void main() {
            vec4 worldPos = modelMatrix * vec4(vertexPosition, 1.0);
            fragmentPosition = worldPos.xyz;
            
            v_clip_pos = orthoProjectionMatrix * viewMatrix * worldPos;
            gl_Position = v_clip_pos;
        }
    ''',

    "fragment_shader" : '''
        #version 330 core
        #extension GL_OES_standard_derivatives : enable

        in vec3 fragmentPosition;
        in vec4 v_clip_pos;

        out vec4 outputColour;

        uniform vec4 objectColour;
        uniform vec3 lightPosition;
        uniform vec3 lightColor = vec3(1.0, 1.0, 1.0);
        uniform float ambientStrength = 0.3;
        uniform float diffuseStrength = 0.7;

        void main() {
            // Calculate normals from derivatives in screen space
            vec3 ndc_pos = v_clip_pos.xyz / v_clip_pos.w;
            vec3 dx = dFdx(ndc_pos);
            vec3 dy = dFdy(ndc_pos);
            
            vec3 N = normalize(cross(dx, dy));
            N *= sign(N.z);
            
            // Light direction (from top-down for minimap)
            vec3 L = normalize(vec3(0.0, 0.0, 1.0));
            float NdotL = max(dot(N, L), 0.0);
            
            // Calculate lighting
            vec3 ambient = ambientStrength * lightColor;
            vec3 diffuse = diffuseStrength * NdotL * lightColor;
            
            // Combine lighting components
            vec3 result = (ambient + diffuse) * objectColour.rgb;
            outputColour = vec4(result, objectColour.a);
        }
    '''
}

######################################################
# Crosshair shader with orthographic projection
crosshair_shader = {
    "vertex_shader" : '''
        #version 330 core
        layout(location = 0) in vec3 vertexPosition;

        uniform mat4 orthoProjectionMatrix;

        void main() {
            gl_Position = orthoProjectionMatrix * vec4(vertexPosition, 1.0);
        }
    ''',

    "fragment_shader" : '''
        #version 330 core

        out vec4 outputColour;

        uniform vec4 crosshairColour;
        uniform float crosshairThickness;
        uniform vec2 screenSize;

        void main() {
            vec2 center = gl_FragCoord.xy - (screenSize / 2.0);
            float horizontalLine = abs(center.y);
            float verticalLine = abs(center.x);
            
            // Create crosshair with anti-aliasing at edges
            if (horizontalLine < crosshairThickness || verticalLine < crosshairThickness) {
                float alpha = 1.0;
                
                // Edge fading for anti-aliasing
                if (horizontalLine > crosshairThickness - 1.0 && horizontalLine < crosshairThickness) {
                    alpha = 1.0 - (horizontalLine - (crosshairThickness - 1.0));
                }
                else if (verticalLine > crosshairThickness - 1.0 && verticalLine < crosshairThickness) {
                    alpha = 1.0 - (verticalLine - (crosshairThickness - 1.0));
                }
                
                outputColour = vec4(crosshairColour.rgb, crosshairColour.a * alpha);
            } else {
                discard;
            }
        }
    '''
}

######################################################
# 3D shape shader with derivative-based normal calculation for enhanced shading
standard_shader = {
    "vertex_shader" : '''
        #version 330 core
        layout(location = 0) in vec3 vertexPosition;
        layout(location = 1) in vec3 vertexNormal;

        uniform mat4 modelMatrix;
        uniform mat4 viewMatrix;
        uniform mat4 projectionMatrix;
        uniform float focalLength;
        
        out vec3 fragmentPosition;
        out vec3 fragmentNormal;
        out vec4 v_clip_pos;

        void main() {
            vec4 worldPos = modelMatrix * vec4(vertexPosition, 1.0);
            fragmentPosition = worldPos.xyz;
            fragmentNormal = mat3(transpose(inverse(modelMatrix))) * vertexNormal;
            
            vec4 camCoordPos = viewMatrix * worldPos;
            v_clip_pos = projectionMatrix * vec4(focalLength * (camCoordPos[0] / abs(camCoordPos[2])), 
                                           focalLength * (camCoordPos[1] / abs(camCoordPos[2])), 
                                           camCoordPos[2], 1.0);
            gl_Position = v_clip_pos;
        }
    ''',

    "fragment_shader" : '''
        #version 330 core
        #extension GL_OES_standard_derivatives : enable

        in vec3 fragmentPosition;
        in vec3 fragmentNormal;
        in vec4 v_clip_pos;

        out vec4 outputColour;

        uniform vec4 objectColour;
        uniform vec3 camPosition;
        uniform vec3 lightPosition;
        uniform vec3 lightColor = vec3(1.0, 1.0, 1.0);
        uniform float ambientStrength = 0.2;
        uniform float diffuseStrength = 1.0;
        uniform float specularStrength = 0.5;
        uniform float shininess = 32.0;
        uniform bool useGeometryNormals = true;

        void main() {
            vec3 N;
            
            if (useGeometryNormals) {
                // Use the normal from the vertex shader (traditional approach)
                N = normalize(fragmentNormal);
            } else {
                // Calculate normals from derivatives in screen space (better for flat surfaces)
                vec3 ndc_pos = v_clip_pos.xyz / v_clip_pos.w;
                vec3 dx = dFdx(ndc_pos);
                vec3 dy = dFdy(ndc_pos);
                
                N = normalize(cross(dx, dy));
                N *= sign(N.z);
            }
            
            // Ambient component
            vec3 ambient = ambientStrength * lightColor;
            
            // Diffuse component
            vec3 lightDir = normalize(lightPosition - fragmentPosition);
            float diff = max(dot(N, lightDir), 0.0);
            vec3 diffuse = diffuseStrength * diff * lightColor;
            
            // Specular component
            vec3 viewDir = normalize(camPosition - fragmentPosition);
            vec3 reflectDir = reflect(-lightDir, N);
            float spec = pow(max(dot(viewDir, reflectDir), 0.0), shininess);
            vec3 specular = specularStrength * spec * lightColor;
            
            // Combine all lighting components
            vec3 result = (ambient + diffuse + specular) * objectColour.rgb;
            outputColour = vec4(result, objectColour.a);
        }
    '''
}
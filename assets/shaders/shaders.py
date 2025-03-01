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

######################################################
# Glowing 3D shape shader with additional glow effect
laser_shader = {
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
        
        // Glow parameters
        uniform float glowIntensity = 2.0;      // Overall glow brightness
        uniform float pulseAmount = 0.3;        // How much pulsing (0 = no pulse)
        uniform float time = 0.0;               // For animation effects
        
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
            
            // Calculate pulse effect
            float pulse = 1.0;
            if (pulseAmount > 0.0) {
                pulse = 1.0 + pulseAmount * sin(time * 3.0);
            }
            
            // Ambient component (enhanced by glow)
            vec3 ambient = ambientStrength * lightColor * glowIntensity * pulse;
            
            // Diffuse component
            vec3 lightDir = normalize(lightPosition - fragmentPosition);
            float diff = max(dot(N, lightDir), 0.0);
            vec3 diffuse = diffuseStrength * diff * lightColor;
            
            // Specular component (enhanced for glow effect)
            vec3 viewDir = normalize(camPosition - fragmentPosition);
            vec3 reflectDir = reflect(-lightDir, N);
            float spec = pow(max(dot(viewDir, reflectDir), 0.0), shininess);
            vec3 specular = specularStrength * spec * lightColor * glowIntensity * pulse;
            
            // Add rim lighting for glow effect at edges
            float rim = 1.0 - max(dot(viewDir, N), 0.0);
            rim = smoothstep(0.4, 1.0, rim);
            vec3 rimLight = rim * objectColour.rgb * glowIntensity * pulse;
            
            // Combine all lighting components
            vec3 result = (ambient + diffuse + specular + rimLight) * objectColour.rgb;
            
            // Enhance brightness for glow effect
            result = min(vec3(1.0, 1.0, 1.0), result * pulse);
            
            outputColour = vec4(result, objectColour.a);
        }
    '''
}

######################################################
# Enhanced glowing destination shader
destination_shader = {
    "vertex_shader": '''
        #version 330 core
        layout(location = 0) in vec3 vertexPosition;
        layout(location = 1) in vec3 vertexNormal;

        uniform mat4 modelMatrix;
        uniform mat4 viewMatrix;
        uniform mat4 projectionMatrix;
        
        out vec3 fragmentPosition;
        out vec3 fragmentNormal;

        void main() {
            vec4 worldPos = modelMatrix * vec4(vertexPosition, 1.0);
            fragmentPosition = worldPos.xyz;
            fragmentNormal = mat3(transpose(inverse(modelMatrix))) * vertexNormal;
            gl_Position = projectionMatrix * viewMatrix * worldPos;
        }
    ''',

    "fragment_shader": '''
        #version 330 core
        in vec3 fragmentPosition;
        in vec3 fragmentNormal;

        out vec4 outputColour;

        uniform vec4 objectColour;
        uniform vec3 camPosition;
        uniform vec3 lightPosition;

        void main() {
            vec3 normal = normalize(fragmentNormal);
            vec3 viewDir = normalize(camPosition - fragmentPosition);
            vec3 lightDir = normalize(lightPosition - fragmentPosition);
            
            // Basic diffuse lighting
            float diff = max(dot(normal, lightDir), 0.0);
            
            // Enhanced rim lighting (glow at edges)
            float rim = 1.0 - max(dot(viewDir, normal), 0.0);
            rim = smoothstep(0.3, 1.0, rim);  // Enhanced rim effect (0.3 instead of 0.5)
            
            // Distinct glowing color (bright gold)
            vec3 glowColor = vec3(1.0, 0.9, 0.4) * 1.8;  // Much brighter gold
            
            // Base color with enhanced rim glow
            vec3 finalColor = mix(objectColour.rgb, glowColor, rim * 0.8);  // More glow (0.8 instead of 0.6)
            
            // Boost contrast and brightness
            finalColor = finalColor * (diff * 0.5 + 0.8);  // Better light response
            
            // Make it even brighter overall
            finalColor *= 1.8;  // Higher boost (1.8 instead of 1.5)
            
            outputColour = vec4(finalColor, objectColour.a);
        }
    '''
}
######################################################
# Write other shaders for minimap and crosshair (Since they need orthographic projection)

# Following is the standard perspective projection shader with uniform colour to all vertices. Can modify as required
standard_shader = {
    "vertex_shader" : '''
        
        #version 330 core
        layout(location = 0) in vec3 vertexPosition;

        uniform mat4 modelMatrix;
        uniform mat4 viewMatrix;
        uniform mat4 projectionMatrix;
        uniform float focalLength;

        void main() {
            vec4 camCoordPos = viewMatrix * modelMatrix * vec4(vertexPosition, 1.0);
            gl_Position = projectionMatrix * vec4(focalLength * (camCoordPos[0] / abs(camCoordPos[2])), focalLength * (camCoordPos[1] / abs(camCoordPos[2])), camCoordPos[2], 1.0);
        }

        ''',

        "fragment_shader" : '''

        #version 330 core

        out vec4 outputColour;

        uniform vec4 objectColour;
        uniform vec3 camPosition;

        void main() {
            vec3 camPos = camPosition;
            outputColour = objectColour;
        }

        '''

}
######################################################
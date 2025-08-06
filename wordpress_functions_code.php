<?php
// Agregar este código al functions.php de tu tema WordPress

// Habilitar meta fields Yoast en REST API
add_action('rest_api_init', function () {
    // Registrar meta fields de Yoast SEO para que sean accesibles via REST API
    register_rest_field('post', 'yoast_meta', array(
        'get_callback' => function($post) {
            return array(
                'title' => get_post_meta($post['id'], '_yoast_wpseo_title', true),
                'metadesc' => get_post_meta($post['id'], '_yoast_wpseo_metadesc', true),
                'focuskw' => get_post_meta($post['id'], '_yoast_wpseo_focuskw', true),
            );
        },
        'update_callback' => function($value, $post) {
            if (isset($value['title'])) {
                update_post_meta($post->ID, '_yoast_wpseo_title', $value['title']);
            }
            if (isset($value['metadesc'])) {
                update_post_meta($post->ID, '_yoast_wpseo_metadesc', $value['metadesc']);
            }
            if (isset($value['focuskw'])) {
                update_post_meta($post->ID, '_yoast_wpseo_focuskw', $value['focuskw']);
            }
            return true;
        },
        'schema' => array(
            'type' => 'object',
            'properties' => array(
                'title' => array('type' => 'string'),
                'metadesc' => array('type' => 'string'),
                'focuskw' => array('type' => 'string'),
            )
        )
    ));

    // También registrar meta fields individuales
    register_meta('post', '_yoast_wpseo_title', array(
        'show_in_rest' => true,
        'type' => 'string',
        'single' => true,
        'auth_callback' => function() {
            return current_user_can('edit_posts');
        }
    ));

    register_meta('post', '_yoast_wpseo_metadesc', array(
        'show_in_rest' => true,
        'type' => 'string', 
        'single' => true,
        'auth_callback' => function() {
            return current_user_can('edit_posts');
        }
    ));

    register_meta('post', '_yoast_wpseo_focuskw', array(
        'show_in_rest' => true,
        'type' => 'string',
        'single' => true, 
        'auth_callback' => function() {
            return current_user_can('edit_posts');
        }
    ));

    register_meta('post', '_yoast_wpseo_canonical', array(
        'show_in_rest' => true,
        'type' => 'string',
        'single' => true,
        'auth_callback' => function() {
            return current_user_can('edit_posts');
        }
    ));

    register_meta('post', '_yoast_wpseo_opengraph-title', array(
        'show_in_rest' => true,
        'type' => 'string',
        'single' => true,
        'auth_callback' => function() {
            return current_user_can('edit_posts');
        }
    ));

    register_meta('post', '_yoast_wpseo_opengraph-description', array(
        'show_in_rest' => true,
        'type' => 'string',
        'single' => true,
        'auth_callback' => function() {
            return current_user_can('edit_posts');
        }
    ));
});

// Alternativa: Hook directo para meta updates via REST
add_action('wp_after_insert_post', function($post_id, $post, $update, $post_before) {
    // Permitir que el REST API actualice meta fields después de crear/actualizar posts
    if (defined('REST_REQUEST') && REST_REQUEST && $update) {
        // Los meta fields se actualizarán automáticamente
        error_log("Meta fields updated for post: " . $post_id);
    }
}, 10, 4);